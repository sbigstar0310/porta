import 'package:dio/dio.dart';
import 'package:pretty_dio_logger/pretty_dio_logger.dart';
import 'package:flutter/foundation.dart';
import 'dart:async';
import 'storage_service.dart';

class DioClient {
  static const String baseUrl = 'http://localhost:8000';

  late final Dio _dio;

  // 토큰 갱신 관련 필드들
  bool _isRefreshing = false;
  Completer<String?>? _refreshCompleter;
  final List<RequestOptions> _failedRequests = [];

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
      final newToken = await _refreshAccessToken();

      if (newToken != null) {
        // 새 토큰으로 원래 요청 재시도
        await _retryRequestWithNewToken(requestOptions, newToken, handler);
      } else {
        // 토큰 갱신 실패 시 로그아웃 처리
        await _handleRefreshTokenExpired();
        handler.next(error);
      }
    } catch (e) {
      // 토큰 갱신 중 오류 발생
      debugPrint('토큰 갱신 중 오류 발생: $e');
      await _handleRefreshTokenExpired();
      handler.next(error);
    }
  }

  /// 토큰 갱신 처리 (중복 요청 방지)
  Future<String?> _refreshAccessToken() async {
    // 이미 갱신 중이면 대기
    if (_isRefreshing) {
      return await _refreshCompleter?.future;
    }

    _isRefreshing = true;
    _refreshCompleter = Completer<String?>();

    try {
      final refreshToken = await StorageService.getRefreshToken();

      if (refreshToken == null ||
          refreshToken.isEmpty ||
          refreshToken == 'dummy_token') {
        debugPrint('유효하지 않은 refresh token');
        _refreshCompleter!.complete(null);
        return null;
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
          // 새 토큰들 저장
          await StorageService.saveAuthToken(newAccessToken);
          if (newRefreshToken != null) {
            await StorageService.saveRefreshToken(newRefreshToken);
          }

          debugPrint('토큰 갱신 성공');
          _refreshCompleter!.complete(newAccessToken);
          return newAccessToken;
        }
      }

      debugPrint('토큰 갱신 실패: 응답 데이터 오류');
      _refreshCompleter!.complete(null);
      return null;
    } catch (e) {
      debugPrint('토큰 갱신 요청 실패: $e');
      _refreshCompleter!.complete(null);
      return null;
    } finally {
      _isRefreshing = false;
      _refreshCompleter = null;
    }
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

  /// Refresh token 만료 시 처리
  Future<void> _handleRefreshTokenExpired() async {
    debugPrint('Refresh token 만료 - 로그아웃 처리');

    // 모든 토큰 삭제
    await StorageService.deleteAuthToken();
    await StorageService.deleteRefreshToken();
    await StorageService.deleteUserData();

    // TODO: 로그아웃 이벤트 발생 (BLoC 등으로 알림)
    // 예: AuthBloc.add(LogoutEvent());
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
