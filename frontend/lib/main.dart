import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:flutter_dotenv/flutter_dotenv.dart';
import 'app.dart';
import 'utils/auth_fragment_cleaner.dart';

void main() async {
  // Flutter 바인딩 초기화
  WidgetsFlutterBinding.ensureInitialized();

  // Supabase 인증 리다이렉트 fragment(#access_token=...) 정리
  // 해시 라우팅에서 fragment가 경로로 파싱되므로 라우터 생성 전에 제거해야 함
  cleanAuthFragment();

  // 로컬 개발 환경에서만 .env 파일 로드
  if (kDebugMode) {
    try {
      await dotenv.load(fileName: ".env");
      debugPrint('✅ .env 파일 로드 완료');
    } catch (e) {
      debugPrint('⚠️  .env 파일을 찾을 수 없음, 환경 변수 사용: $e');
    }
  }

  runApp(const PortaApp());
}
