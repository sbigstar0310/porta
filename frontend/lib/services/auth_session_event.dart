/// DioClient에서 발생하는 인증 세션 이벤트
///
/// 네트워크 계층(DioClient)이 BLoC에 직접 의존하지 않도록,
/// 인증 관련 사건을 스트림 이벤트로 발행하고 앱 레벨에서 구독한다.
abstract class AuthSessionEvent {
  const AuthSessionEvent();
}

/// 이메일 인증 완료가 확인됨 (재로그인 필요)
class EmailVerificationCompleted extends AuthSessionEvent {
  final String message;

  const EmailVerificationCompleted(this.message);
}

/// Refresh token 만료로 세션이 종료됨 (토큰은 이미 삭제된 상태)
class SessionExpired extends AuthSessionEvent {
  const SessionExpired();
}
