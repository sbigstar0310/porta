import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:flutter_dotenv/flutter_dotenv.dart';
import 'app.dart';

void main() async {
  // Flutter 바인딩 초기화
  WidgetsFlutterBinding.ensureInitialized();

  // 로컬 개발 환경에서만 .env 파일 로드
  if (kDebugMode) {
    try {
      await dotenv.load(fileName: ".env");
      print('✅ .env 파일 로드 완료');
    } catch (e) {
      print('⚠️  .env 파일을 찾을 수 없음, 환경 변수 사용: $e');
    }
  }

  runApp(const PortaApp());
}
