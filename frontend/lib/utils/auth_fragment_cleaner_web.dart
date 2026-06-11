// ignore: deprecated_member_use
import 'dart:html' as html;

/// Supabase 이메일 인증 리다이렉트가 남긴 URL fragment(#access_token=... 또는
/// #error=...)를 go_router가 파싱하기 전에 제거한다.
/// 해시 라우팅에서는 fragment가 곧 경로라서, 그대로 두면 라우터가 크래시한다.
void cleanAuthFragment() {
  final fragment = html.window.location.hash;
  final isAuthCallback =
      fragment.startsWith('#access_token') ||
      fragment.startsWith('#error') ||
      fragment.contains('type=signup') ||
      fragment.contains('type=recovery');

  if (isAuthCallback) {
    html.window.history.replaceState(
      null,
      '',
      '${html.window.location.pathname}#/login',
    );
  }
}
