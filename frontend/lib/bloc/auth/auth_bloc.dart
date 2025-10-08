import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:flutter/foundation.dart';
import 'dart:convert';
import '../../services/api_service.dart';
import '../../services/storage_service.dart';
import '../../models/user.dart';
import 'auth_event.dart';
import 'auth_state.dart';

class AuthBloc extends Bloc<AuthEvent, AuthState> {
  final ApiService _apiService = ApiService();

  AuthBloc() : super(AuthInitial()) {
    on<AuthInitialized>(_onInitialized);
    on<AuthLoginRequested>(_onLoginRequested);
    on<AuthRegisterRequested>(_onRegisterRequested);
    on<AuthLogoutRequested>(_onLogoutRequested);
    on<AuthUserFetched>(_onUserFetched);
    on<AuthDeleteRequested>(_onDeleteRequested);
  }

  Future<void> _onInitialized(
    AuthInitialized event,
    Emitter<AuthState> emit,
  ) async {
    emit(AuthLoading());

    try {
      final token = await StorageService.getAuthToken();

      if (token != null && token != 'dummy_token') {
        _apiService.setAuthToken(token);
        debugPrint('토큰 설정 완료, 사용자 정보 조회 시도');
        final user = await _apiService.getCurrentUser();
        emit(AuthAuthenticated(user));
      } else {
        debugPrint('유효한 토큰 없음 - 로그인 필요');
        emit(AuthUnauthenticated());
      }
    } catch (e) {
      debugPrint('앱 초기화 오류: $e');
      // 이메일 미인증 오류인지 확인
      if (e.toString().contains('EMAIL_NOT_VERIFIED')) {
        debugPrint('이메일 미인증 상태 감지');
        // 저장된 사용자 데이터가 있다면 이메일 미인증 상태로 설정
        try {
          final userDataString = await StorageService.getUserData();
          if (userDataString != null) {
            final userJson = json.decode(userDataString);
            final user = User.fromJson(userJson);
            emit(AuthEmailNotVerified(user));
            return;
          }
        } catch (_) {}
      }
      emit(AuthUnauthenticated());
    }
  }

  Future<void> _onLoginRequested(
    AuthLoginRequested event,
    Emitter<AuthState> emit,
  ) async {
    emit(AuthLoading());

    try {
      final user = await _apiService.login(event.email, event.password);

      // 실제 토큰 저장 및 API 서비스에 설정
      if (user.accessToken != null) {
        await StorageService.saveAuthToken(user.accessToken!);
        _apiService.setAuthToken(user.accessToken!);
      } else {
        throw Exception('accessToken is null');
      }

      // 리프레시 토큰도 저장
      if (user.refreshToken != null) {
        await StorageService.saveRefreshToken(user.refreshToken!);
      } else {
        throw Exception('refreshToken is null');
      }

      // 사용자 정보를 JSON 문자열로 변환하여 저장
      await StorageService.saveUserData(json.encode(user.toJson()));

      emit(AuthAuthenticated(user));
    } catch (e) {
      // 이메일 미인증 오류인지 확인
      if (e.toString().contains('EMAIL_NOT_VERIFIED')) {
        debugPrint('로그인 후 이메일 미인증 상태 감지');
        // 로그인 시에는 저장된 사용자 데이터가 없으므로 입력받은 이메일로 임시 User 객체 생성
        final tempUser = User(
          id: 0, // 임시 ID
          email: event.email,
          timezone: 'Asia/Seoul',
          language: 'ko',
          emailVerified: false,
          createdAt: DateTime.now(),
          updatedAt: DateTime.now(),
          lastLogin: DateTime.now(),
        );
        emit(AuthEmailNotVerified(tempUser));
        return;
      }
      emit(AuthError('로그인 실패: $e'));
    }
  }

  Future<void> _onRegisterRequested(
    AuthRegisterRequested event,
    Emitter<AuthState> emit,
  ) async {
    emit(AuthLoading());

    try {
      // 회원가입 전 기존 토큰 정리
      await StorageService.deleteAuthToken();
      await StorageService.deleteRefreshToken();

      final user = await _apiService.register(
        event.email,
        event.password,
        event.name,
      );

      // 사용자 정보를 JSON 문자열로 변환하여 저장
      await StorageService.saveUserData(json.encode(user.toJson()));

      // 이메일 인증 상태에 따라 다른 상태로 변경
      if (user.emailVerified) {
        emit(AuthAuthenticated(user));
      } else {
        emit(AuthEmailNotVerified(user));
      }
    } catch (e) {
      emit(AuthError('회원가입 실패: $e'));
    }
  }

  Future<void> _onLogoutRequested(
    AuthLogoutRequested event,
    Emitter<AuthState> emit,
  ) async {
    emit(AuthLoading());

    try {
      // 백엔드 signout API 호출
      await _apiService.signout();

      // 로컬 저장소 정리
      await StorageService.deleteAuthToken();
      await StorageService.deleteRefreshToken();
      await StorageService.deleteUserData();

      emit(AuthUnauthenticated());
    } catch (e) {
      // 백엔드 호출 실패해도 로컬 정리는 진행
      await StorageService.deleteAuthToken();
      await StorageService.deleteRefreshToken();
      await StorageService.deleteUserData();

      emit(AuthUnauthenticated());
    }
  }

  Future<void> _onUserFetched(
    AuthUserFetched event,
    Emitter<AuthState> emit,
  ) async {
    try {
      final user = await _apiService.getCurrentUser();
      emit(AuthAuthenticated(user));
    } catch (e) {
      // 이메일 미인증 오류인지 확인
      if (e.toString().contains('EMAIL_NOT_VERIFIED')) {
        debugPrint('사용자 정보 조회 중 이메일 미인증 상태 감지');
        try {
          final userDataString = await StorageService.getUserData();
          if (userDataString != null) {
            final userJson = json.decode(userDataString);
            final user = User.fromJson(userJson);
            emit(AuthEmailNotVerified(user));
            return;
          }
        } catch (_) {}
      }
      emit(AuthError('사용자 정보 조회 실패: $e'));
    }
  }

  Future<void> _onDeleteRequested(
    AuthDeleteRequested event,
    Emitter<AuthState> emit,
  ) async {
    try {
      // 현재 인증된 사용자 정보 확인 (emit 전에 확인해야 함!)
      final currentState = state;

      if (currentState is! AuthAuthenticated) {
        emit(AuthError('로그인이 필요합니다'));
        return;
      }

      // 토큰 상태 확인
      final token = await StorageService.getAuthToken();
      debugPrint('현재 저장된 토큰: $token');

      if (token == null || token == 'dummy_token') {
        debugPrint('유효한 토큰이 없음');
        emit(AuthError('인증 토큰이 없습니다. 다시 로그인해주세요.'));
        return;
      }

      // 인증 상태 확인 후에 로딩 상태로 변경
      emit(AuthLoading());

      debugPrint('회원 탈퇴 시작 - 인증된 사용자: ${currentState.user.email}');

      // JWT 토큰 기반으로 현재 사용자 삭제
      await _apiService.deleteCurrentUser();

      debugPrint('백엔드 사용자 삭제 완료');

      // 로컬 저장소 정리
      await StorageService.deleteAuthToken();
      await StorageService.deleteRefreshToken();
      await StorageService.deleteUserData();

      debugPrint('로컬 저장소 정리 완료');

      emit(AuthUnauthenticated());
    } catch (e) {
      debugPrint('회원 탈퇴 오류 상세: $e');
      emit(AuthError('회원 탈퇴 실패: $e'));
    }
  }
}
