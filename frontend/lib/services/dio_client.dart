import 'package:dio/dio.dart';
import 'package:pretty_dio_logger/pretty_dio_logger.dart';
import 'package:flutter/foundation.dart';
import 'package:flutter_dotenv/flutter_dotenv.dart';
import 'dart:async';
import 'storage_service.dart';
import 'auth_session_event.dart';
import 'dart:convert';

/// 토큰 갱신 결과 분류
/// - success: 갱신 성공 (새 액세스 토큰 발급)
/// - invalidSession: 리프레시 토큰이 확정적으로 무효(401/4xx) 또는 없음 → 재로그인 필요
/// - transient: 일시적 실패(500·타임아웃·네트워크) → 세션 유지, 다음에 재시도
enum RefreshOutcome { success, invalidSession, transient }

class RefreshResult {
  final RefreshOutcome outcome;
  final String? token;
  const RefreshResult(this.outcome, [this.token]);
}

class DioClient {
  // 인증 세션 이벤트 스트림 (이메일 인증 완료, 세션 만료 등)
  final StreamController<AuthSessionEvent> _authEventController =
      StreamController<AuthSessionEvent>.broadcast();

  /// 앱 레벨에서 구독하여 AuthBloc 이벤트로 변환한다
  Stream<AuthSessionEvent> get authEvents => _authEventController.stream;

  // .env 파일에서 API_URL을 가져오고, 없으면 fallback URL 사용
  static String get baseUrl {
    String url;

    try {
      // dotenv가 초기화된 경우에만 접근 시도
      url =
          dotenv.env['API_URL'] ??
          const String.fromEnvironment(
            'API_URL',
            defaultValue: 'http://localhost:8000',
          );
    } catch (e) {
      // dotenv가 초기화되지 않은 경우 환경 변수나 기본값 사용
      url = const String.fromEnvironment(
        'API_URL',
        defaultValue: 'http://localhost:8000',
      );
      if (kDebugMode) {
        debugPrint('⚠️  dotenv not initialized, using fallback: $e');
      }
    }

    debugPrint('🌐 API Base URL: $url');

    return url;
  }

  late final Dio _dio;

  // 토큰 갱신 관련 필드들
  bool _isRefreshing = false;
  Completer<RefreshResult>? _refreshCompleter;

  // 싱글톤 패턴 구현
  static final DioClient _instance = DioClient._internal();
  factory DioClient() => _instance;

  DioClient._internal() {
    _dio = Dio();
    _setupDio();
  }

  void _setupDio() {
    // 기본 설정
    _dio.options = BaseOptions(
      baseUrl: baseUrl,
      connectTimeout: const Duration(seconds: 30),
      receiveTimeout: const Duration(seconds: 30),
      sendTimeout: const Duration(seconds: 30),
      headers: {'Content-Type': 'application/json'},
    );

    // 인터셉터 추가
    _dio.interceptors.add(_createAuthInterceptor());

    // 로깅 인터셉터 추가 (개발 모드에서만)
    if (kDebugMode) {
      _dio.interceptors.add(
        PrettyDioLogger(
          requestHeader: true,
          requestBody: true,
          responseBody: true,
          responseHeader: false,
          error: true,
          compact: true,
          maxWidth: 90,
          enabled: kDebugMode,
        ),
      );
    }
  }

  InterceptorsWrapper _createAuthInterceptor() {
    return InterceptorsWrapper(
      onRequest: (options, handler) async {
        await _addAuthHeader(options);
        handler.next(options);
      },
      onError: (error, handler) async {
        if (error.response?.statusCode == 401) {
          await _handleUnauthorizedError(error, handler);
        } else if (error.response?.statusCode == 403) {
          await _handleForbiddenError(error, handler);
        } else {
          handler.next(error);
        }
      },
    );
  }

  /// Authorization 헤더 추가
  Future<void> _addAuthHeader(RequestOptions options) async {
    // refresh 요청에는 토큰을 추가하지 않음
    if (options.path.contains('/auth/refresh')) {
      return;
    }

    final token = await StorageService.getAuthToken();
    if (token != null && token.isNotEmpty && token != 'dummy_token') {
      options.headers['Authorization'] = 'Bearer $token';
    }
  }

  /// 401 에러 처리 및 토큰 갱신
  Future<void> _handleUnauthorizedError(
    DioException error,
    ErrorInterceptorHandler handler,
  ) async {
    final requestOptions = error.requestOptions;

    // refresh 요청 자체가 401이면 로그아웃 처리
    if (requestOptions.path.contains('/auth/refresh')) {
      await _handleRefreshTokenExpired();
      handler.next(error);
      return;
    }

    try {
      // 토큰 갱신 시도
      final result = await _refreshAccessToken();

      switch (result.outcome) {
        case RefreshOutcome.success:
          // 새 토큰으로 원래 요청 재시도
          await _retryRequestWithNewToken(requestOptions, result.token!, handler);
          return;
        case RefreshOutcome.transient:
          // 일시적 실패(500·네트워크 등) → 세션 유지, 원 요청만 실패 처리(다음에 재시도됨)
          debugPrint('토큰 갱신 일시 실패 - 세션 유지, 원 요청 실패 처리');
          handler.next(error);
          return;
        case RefreshOutcome.invalidSession:
          // 회전 레이스 복구: 다른 탭/흐름이 이미 갱신해 저장소 토큰이 바뀌었으면 그 토큰으로 1회 재시도
          final currentToken = await StorageService.getAuthToken();
          final attempted = requestOptions.headers['Authorization'];
          if (currentToken != null &&
              currentToken.isNotEmpty &&
              currentToken != 'dummy_token' &&
              'Bearer $currentToken' != attempted) {
            debugPrint('저장소 토큰이 갱신됨(다른 흐름) - 새 토큰으로 재시도');
            await _retryRequestWithNewToken(requestOptions, currentToken, handler);
            return;
          }
          // 확정적으로 무효한 세션 → 로그아웃 + 재로그인 유도
          await _handleRefreshTokenExpired();
          handler.next(error);
          return;
      }
    } catch (e) {
      // 예기치 못한 오류: 세션을 지우지 않고(불필요한 로그아웃 방지) 원 요청만 실패 처리
      debugPrint('토큰 갱신 처리 중 예기치 못한 오류(세션 유지): $e');
      handler.next(error);
    }
  }

  /// 토큰 갱신 처리 (중복 요청 방지, single-flight)
  ///
  /// 실패를 확정 무효(invalidSession)와 일시 오류(transient)로 구분한다.
  /// - 4xx (백엔드가 무효 리프레시 토큰에 반환하는 401 포함) 또는 리프레시 토큰 없음 → invalidSession
  /// - 5xx · 타임아웃 · 네트워크(응답 없음) → transient (세션 유지)
  Future<RefreshResult> _refreshAccessToken() async {
    // 이미 갱신 중이면 그 결과를 공유 (탭 내 동시 401을 한 번의 갱신으로 합침)
    if (_isRefreshing) {
      return await _refreshCompleter?.future ??
          const RefreshResult(RefreshOutcome.transient);
    }

    _isRefreshing = true;
    final completer = Completer<RefreshResult>();
    _refreshCompleter = completer;

    try {
      final refreshToken = await StorageService.getRefreshToken();

      if (refreshToken == null ||
          refreshToken.isEmpty ||
          refreshToken == 'dummy_token') {
        debugPrint('유효하지 않은 refresh token - 세션 무효');
        return _complete(completer, const RefreshResult(RefreshOutcome.invalidSession));
      }

      debugPrint('토큰 갱신 시도 중...');

      // 새로운 Dio 인스턴스로 refresh 요청 (인터셉터 없이)
      final refreshDio = Dio(BaseOptions(baseUrl: baseUrl));

      final response = await refreshDio.post(
        '/auth/refresh',
        data: FormData.fromMap({'refresh_token': refreshToken}),
        options: Options(contentType: 'application/x-www-form-urlencoded'),
      );

      if (response.statusCode == 200) {
        final responseData = response.data;
        final newAccessToken = responseData['access_token'];
        final newRefreshToken = responseData['refresh_token'];

        if (newAccessToken != null) {
          // 새 토큰들 저장 (리프레시 토큰 회전 반영)
          await StorageService.saveAuthToken(newAccessToken);
          if (newRefreshToken != null) {
            await StorageService.saveRefreshToken(newRefreshToken);
          }

          debugPrint('토큰 갱신 성공');
          return _complete(
            completer,
            RefreshResult(RefreshOutcome.success, newAccessToken),
          );
        }
      }

      // 200인데 토큰이 없는 비정상 응답 → 일시 오류로 취급(세션 유지)
      debugPrint('토큰 갱신 실패: 응답 데이터 오류');
      return _complete(completer, const RefreshResult(RefreshOutcome.transient));
    } on DioException catch (e) {
      final statusCode = e.response?.statusCode;
      // 4xx(401 INVALID_REFRESH_TOKEN 등): 리프레시 토큰 확정 무효 → 재로그인
      if (statusCode != null && statusCode >= 400 && statusCode < 500) {
        debugPrint('토큰 갱신 확정 실패(status=$statusCode) - 세션 무효');
        return _complete(completer, const RefreshResult(RefreshOutcome.invalidSession));
      }
      // 5xx · 타임아웃 · 응답 없음(네트워크): 일시 오류 → 세션 유지
      debugPrint('토큰 갱신 일시 실패(status=$statusCode, type=${e.type})');
      return _complete(completer, const RefreshResult(RefreshOutcome.transient));
    } catch (e) {
      // 예기치 못한 오류: 세션을 지우지 않도록 일시 오류로 취급
      debugPrint('토큰 갱신 요청 예외(일시 취급): $e');
      return _complete(completer, const RefreshResult(RefreshOutcome.transient));
    } finally {
      _isRefreshing = false;
      _refreshCompleter = null;
    }
  }

  /// completer를 완료시키고 같은 결과를 반환하는 헬퍼 (single-flight 대기자에게 전파)
  RefreshResult _complete(Completer<RefreshResult> completer, RefreshResult result) {
    if (!completer.isCompleted) {
      completer.complete(result);
    }
    return result;
  }

  /// 새 토큰으로 원래 요청 재시도
  Future<void> _retryRequestWithNewToken(
    RequestOptions requestOptions,
    String newToken,
    ErrorInterceptorHandler handler,
  ) async {
    try {
      // 새 토큰으로 헤더 업데이트
      requestOptions.headers['Authorization'] = 'Bearer $newToken';

      // 원래 요청 재시도
      final response = await _dio.fetch(requestOptions);
      handler.resolve(response);
    } catch (e) {
      // 재시도도 실패하면 원래 에러 전달
      debugPrint('토큰 갱신 후 재시도 실패: $e');
      handler.next(DioException(requestOptions: requestOptions, error: e));
    }
  }

  /// 403 Forbidden 에러 처리 (이메일 인증 확인 포함)
  Future<void> _handleForbiddenError(
    DioException error,
    ErrorInterceptorHandler handler,
  ) async {
    // 현재 사용자 정보 확인
    final userData = await StorageService.getUserData();
    if (userData != null) {
      try {
        final user = json.decode(userData);
        final emailVerified = user['email_verified'] as bool? ?? false;

        // 사용자의 emailVerified가 false인 경우에만 이메일 인증 확인 시도
        if (!emailVerified) {
          final isVerified = await _checkEmailVerification();
          if (isVerified) {
            // 인증이 완료된 경우 성공 알림 및 로그아웃 처리
            await _handleEmailVerificationSuccess();
            handler.next(error); // 원래 에러를 그대로 전달하여 로그아웃 처리
            return;
          }
        }
      } catch (e) {
        debugPrint('사용자 데이터 파싱 오류: $e');
      }
    }

    // 일반적인 403 에러 처리
    handler.next(error);
  }

  /// 이메일 인증 상태 확인
  Future<bool> _checkEmailVerification() async {
    try {
      debugPrint('이메일 인증 상태 확인 중...');

      // 로컬 스토리지에서 사용자 이메일 가져오기
      final userData = await StorageService.getUserData();
      if (userData == null) {
        debugPrint('로컬 사용자 데이터 없음');
        return false;
      }

      final user = json.decode(userData);
      final email = user['email'] as String?;
      if (email == null || email.isEmpty) {
        debugPrint('사용자 이메일 정보 없음');
        return false;
      }

      // 새로운 Dio 인스턴스로 이메일 인증 상태 확인 (JWT 토큰 불필요)
      final checkDio = Dio(BaseOptions(baseUrl: baseUrl));
      final response = await checkDio.get(
        '/auth/email-verification-status/$email',
      );

      if (response.statusCode == 200) {
        final responseData = response.data;
        final emailVerified = responseData['email_verified'] as bool? ?? false;
        final requiresRelogin =
            responseData['requires_relogin'] as bool? ?? false;

        if (emailVerified && requiresRelogin) {
          // 로컬 저장소의 사용자 정보 업데이트
          user['email_verified'] = true;
          await StorageService.saveUserData(json.encode(user));
          debugPrint('이메일 인증 완료 확인됨 - 재로그인 필요');
          return true;
        }
      }

      return false;
    } catch (e) {
      debugPrint('이메일 인증 상태 확인 실패: $e');
      return false;
    }
  }

  /// 이메일 인증 성공 처리
  Future<void> _handleEmailVerificationSuccess() async {
    debugPrint('이메일 인증 성공 - 로그아웃 처리 예정');

    _authEventController.add(
      const EmailVerificationCompleted('이메일 인증이 완료되었습니다. 다시 로그인해주세요.'),
    );
  }

  /// Refresh token 만료 시 처리
  Future<void> _handleRefreshTokenExpired() async {
    debugPrint('Refresh token 만료 - 로그아웃 처리');

    // 모든 토큰 삭제
    await StorageService.deleteAuthToken();
    await StorageService.deleteRefreshToken();
    await StorageService.deleteUserData();

    // 앱 레벨에 세션 만료 알림 (AuthBloc이 로그아웃 상태로 전환)
    _authEventController.add(const SessionExpired());
  }

  // GET 요청
  Future<Response<T>> get<T>(
    String path, {
    Map<String, dynamic>? queryParameters,
    Options? options,
    CancelToken? cancelToken,
  }) async {
    try {
      return await _dio.get<T>(
        path,
        queryParameters: queryParameters,
        options: options,
        cancelToken: cancelToken,
      );
    } on DioException catch (e) {
      throw _handleDioError(e);
    }
  }

  // POST 요청
  Future<Response<T>> post<T>(
    String path, {
    dynamic data,
    Map<String, dynamic>? queryParameters,
    Options? options,
    CancelToken? cancelToken,
  }) async {
    try {
      return await _dio.post<T>(
        path,
        data: data,
        queryParameters: queryParameters,
        options: options,
        cancelToken: cancelToken,
      );
    } on DioException catch (e) {
      throw _handleDioError(e);
    }
  }

  // PATCH 요청
  Future<Response<T>> patch<T>(
    String path, {
    dynamic data,
    Map<String, dynamic>? queryParameters,
    Options? options,
    CancelToken? cancelToken,
  }) async {
    try {
      return await _dio.patch<T>(
        path,
        data: data,
        queryParameters: queryParameters,
        options: options,
        cancelToken: cancelToken,
      );
    } on DioException catch (e) {
      throw _handleDioError(e);
    }
  }

  // DELETE 요청
  Future<Response<T>> delete<T>(
    String path, {
    dynamic data,
    Map<String, dynamic>? queryParameters,
    Options? options,
    CancelToken? cancelToken,
  }) async {
    try {
      return await _dio.delete<T>(
        path,
        data: data,
        queryParameters: queryParameters,
        options: options,
        cancelToken: cancelToken,
      );
    } on DioException catch (e) {
      throw _handleDioError(e);
    }
  }

  // Form data POST 요청 (로그인용)
  Future<Response<T>> postForm<T>(
    String path, {
    Map<String, dynamic>? data,
    Options? options,
    CancelToken? cancelToken,
  }) async {
    try {
      return await _dio.post<T>(
        path,
        data: FormData.fromMap(data ?? {}),
        options:
            options?.copyWith(
              contentType: 'application/x-www-form-urlencoded',
            ) ??
            Options(contentType: 'application/x-www-form-urlencoded'),
        cancelToken: cancelToken,
      );
    } on DioException catch (e) {
      throw _handleDioError(e);
    }
  }

  // DioException을 사용자 친화적인 메시지로 변환
  Exception _handleDioError(DioException error) {
    String message;

    switch (error.type) {
      case DioExceptionType.connectionTimeout:
      case DioExceptionType.sendTimeout:
      case DioExceptionType.receiveTimeout:
        message = '서버 연결 시간이 초과되었습니다. 네트워크 상태를 확인해주세요.';
        break;

      case DioExceptionType.connectionError:
        message = '서버에 연결할 수 없습니다. 백엔드 서버가 실행 중인지 확인해주세요.';
        break;

      case DioExceptionType.badResponse:
        final statusCode = error.response?.statusCode;
        final responseData = error.response?.data;

        switch (statusCode) {
          case 400:
            if (responseData is Map && responseData.containsKey('detail')) {
              message = responseData['detail'].toString();
            } else {
              message = '잘못된 요청입니다. 입력 정보를 확인해주세요.';
            }
            break;
          case 401:
            message = '로그인이 필요합니다.';
            break;
          case 403:
            if (responseData is Map &&
                responseData['detail'] == 'EMAIL_NOT_VERIFIED') {
              message = 'EMAIL_NOT_VERIFIED';
            } else {
              message = '접근 권한이 없습니다.';
            }
            break;
          case 404:
            message = '요청한 리소스를 찾을 수 없습니다.';
            break;
          case 409:
            message = '이미 존재하는 데이터입니다.';
            break;
          case 422:
            message = '입력 데이터가 올바르지 않습니다.';
            break;
          case 500:
            message = '서버 내부 오류가 발생했습니다.';
            break;
          default:
            message = '서버 오류가 발생했습니다 ($statusCode)';
        }
        break;

      case DioExceptionType.cancel:
        message = '요청이 취소되었습니다.';
        break;

      case DioExceptionType.unknown:
      default:
        message = '알 수 없는 오류가 발생했습니다.';
        break;
    }

    return Exception(message);
  }

  /// 수동 토큰 갱신 (필요시 외부에서 호출 가능)
  Future<bool> refreshTokenManually() async {
    try {
      final newToken = await _refreshAccessToken();
      return newToken != null;
    } catch (e) {
      debugPrint('수동 토큰 갱신 실패: $e');
      return false;
    }
  }

  // Dio 인스턴스 직접 접근 (필요한 경우)
  Dio get dio => _dio;
}
