import 'dart:convert';
import 'package:http/http.dart' as http;
import '../models/user.dart';
import '../models/portfolio.dart';
import '../models/agent_status.dart';
import '../models/stock_search_result.dart';
import '../models/task_progress.dart';
import 'package:flutter/foundation.dart';
import 'storage_service.dart';

class ApiService {
  static const String baseUrl = 'http://localhost:8000'; // 백엔드 서버 URL

  // 현재 backend는 user_id=1로 고정 (인증 시스템 미구현)
  static const int currentUserId = 1;

  // 싱글톤 패턴 구현
  static final ApiService _instance = ApiService._internal();
  factory ApiService() => _instance;
  ApiService._internal();

  String? _authToken;

  void setAuthToken(String token) {
    _authToken = token;
  }

  Map<String, String> get _headers {
    final headers = {'Content-Type': 'application/json'};

    // 토큰이 있으면 Authorization 헤더 추가
    if (_authToken != null &&
        _authToken!.isNotEmpty &&
        _authToken != 'dummy_token') {
      headers['Authorization'] = 'Bearer $_authToken';
    }

    return headers;
  }

  // Auth endpoints
  Future<User> login(String email, String password) async {
    try {
      debugPrint('로그인 시도: $email');

      // Form data로 전송 (application/x-www-form-urlencoded)
      final response = await http.post(
        Uri.parse('$baseUrl/auth/login'),
        headers: {'Content-Type': 'application/x-www-form-urlencoded'},
        body: {'email': email, 'password': password},
      );

      debugPrint('로그인 응답 상태코드: ${response.statusCode}');
      debugPrint('로그인 응답 body: ${response.body}');

      if (response.statusCode == 200) {
        final userData = json.decode(response.body);
        return User.fromJson(userData);
      } else if (response.statusCode == 400) {
        throw Exception('이메일 또는 비밀번호를 확인해주세요');
      } else if (response.statusCode == 403) {
        // 403 오류 - 이메일 미인증 확인
        try {
          final Map<String, dynamic> errorData = json.decode(response.body);
          final String detail = errorData['detail'] ?? '';
          if (detail == 'EMAIL_NOT_VERIFIED') {
            debugPrint('로그인 시 이메일 미인증 상태 감지');
            throw Exception('EMAIL_NOT_VERIFIED');
          }
        } on FormatException catch (jsonError) {
          debugPrint('JSON 파싱 실패: $jsonError');
        }
        throw Exception('접근 권한이 없습니다');
      } else {
        throw Exception('서버 오류가 발생했습니다 (${response.statusCode})');
      }
    } catch (e) {
      debugPrint('로그인 오류 상세: $e');
      if (e.toString().contains('SocketException') ||
          e.toString().contains('Connection')) {
        throw Exception('서버에 연결할 수 없습니다. 백엔드 서버가 실행 중인지 확인해주세요');
      }
      rethrow;
    }
  }

  Future<User> register(String email, String password, String? name) async {
    try {
      debugPrint('회원가입 시도: $email');

      final requestBody = {
        'email': email,
        'password': password,
        'timezone': 'Asia/Seoul',
        'language': 'ko',
      };

      final response = await http.post(
        Uri.parse('$baseUrl/users'),
        headers: _headers,
        body: json.encode(requestBody),
      );

      debugPrint('회원가입 응답 상태코드: ${response.statusCode}');
      debugPrint('회원가입 응답 body: ${response.body}');

      if (response.statusCode == 201) {
        final userData = json.decode(response.body);
        return User.fromJson(userData);
      } else {
        final errorMessage = response.statusCode == 400
            ? '이미 등록된 이메일이거나 입력 정보를 확인해주세요'
            : '서버 오류가 발생했습니다 (${response.statusCode})';
        throw Exception(errorMessage);
      }
    } catch (e) {
      debugPrint('회원가입 오류 상세: $e');
      if (e.toString().contains('SocketException') ||
          e.toString().contains('Connection')) {
        throw Exception('서버에 연결할 수 없습니다. 백엔드 서버가 실행 중인지 확인해주세요');
      }
      rethrow;
    }
  }

  Future<User> getCurrentUser() async {
    try {
      // 토큰이 있으면 저장된 사용자 정보를 사용 (임시 조치)
      // TODO: 백엔드에 /users/me 엔드포인트 추가 후 토큰 기반 조회로 변경
      if (_authToken != null &&
          _authToken!.isNotEmpty &&
          _authToken != 'dummy_token') {
        final userData = await StorageService.getUserData();
        if (userData != null) {
          debugPrint('저장된 사용자 정보 사용');
          return User.fromJson(json.decode(userData));
        }
      }

      // 토큰이 없으면 기존 방식 사용 (하드코딩된 user ID)
      debugPrint('사용자 정보 조회 시도: $currentUserId');

      final response = await http.get(
        Uri.parse('$baseUrl/users/$currentUserId'),
        headers: _headers,
      );

      debugPrint('사용자 정보 응답 상태코드: ${response.statusCode}');
      debugPrint('사용자 정보 응답 body: ${response.body}');

      if (response.statusCode == 200) {
        final userData = json.decode(response.body);
        return User.fromJson(userData);
      } else {
        throw Exception('사용자 정보를 찾을 수 없습니다 (${response.statusCode})');
      }
    } catch (e) {
      debugPrint('사용자 정보 조회 오류 상세: $e');
      if (e.toString().contains('SocketException') ||
          e.toString().contains('Connection')) {
        throw Exception('서버에 연결할 수 없습니다. 백엔드 서버가 실행 중인지 확인해주세요');
      }
      rethrow;
    }
  }

  // Portfolio endpoints
  Future<Portfolio> getPortfolio() async {
    try {
      debugPrint('포트폴리오 조회 시도');
      debugPrint('현재 토큰: $_authToken');

      // 토큰이 없으면 저장소에서 다시 로드 시도
      if (_authToken == null || _authToken == 'dummy_token') {
        final token = await StorageService.getAuthToken();
        if (token != null && token != 'dummy_token') {
          _authToken = token;
          debugPrint('저장소에서 토큰 복원: $token');
        }
      }

      debugPrint('요청 헤더: $_headers');

      final response = await http.get(
        Uri.parse('$baseUrl/portfolio'),
        headers: _headers,
      );

      debugPrint('포트폴리오 응답 상태코드: ${response.statusCode}');
      debugPrint('포트폴리오 응답 body: ${response.body}');

      if (response.statusCode == 200) {
        final data = json.decode(response.body);
        return Portfolio.fromJson(data);
      } else if (response.statusCode == 401 || response.statusCode == 422) {
        // 인증 실패 - 토큰이 없거나 유효하지 않음
        debugPrint('인증 실패: ${response.statusCode}');
        throw Exception('로그인이 필요합니다');
      } else if (response.statusCode == 403) {
        // 403 오류 - 이메일 미인증 확인
        try {
          final Map<String, dynamic> errorData = json.decode(response.body);
          final String detail = errorData['detail'] ?? '';
          if (detail == 'EMAIL_NOT_VERIFIED') {
            debugPrint('이메일 미인증 상태 감지');
            throw Exception('EMAIL_NOT_VERIFIED');
          }
        } catch (jsonError) {
          debugPrint('JSON 파싱 실패, 기본 403 처리');
        }
        throw Exception('접근 권한이 없습니다');
      } else {
        debugPrint('포트폴리오 조회 실패: ${response.statusCode} - ${response.body}');
        throw Exception('포트폴리오를 조회할 수 없습니다 (${response.statusCode})');
      }
    } catch (e) {
      debugPrint('포트폴리오 조회 오류 상세: $e');
      if (e.toString().contains('SocketException') ||
          e.toString().contains('Connection')) {
        throw Exception('서버에 연결할 수 없습니다. 백엔드 서버가 실행 중인지 확인해주세요');
      }
      rethrow;
    }
  }

  // Backend에서는 포트폴리오 생성이 별도로 없고 기본적으로 존재
  Future<Portfolio> createPortfolio(String name) async {
    // 현재 backend 구조상 포트폴리오는 항상 존재하므로 조회만 수행
    return await getPortfolio();
  }

  Future<Portfolio> updatePortfolio(
    int portfolioId,
    Map<String, dynamic> updates,
  ) async {
    try {
      debugPrint('포트폴리오 업데이트 시도: $updates');

      final response = await http.patch(
        Uri.parse('$baseUrl/portfolio'),
        headers: _headers,
        body: json.encode(updates),
      );

      debugPrint('포트폴리오 업데이트 응답 상태코드: ${response.statusCode}');
      debugPrint('포트폴리오 업데이트 응답 body: ${response.body}');

      if (response.statusCode == 200) {
        final data = json.decode(response.body);
        return Portfolio.fromJson(data);
      } else {
        throw Exception('포트폴리오를 업데이트할 수 없습니다 (${response.statusCode})');
      }
    } catch (e) {
      debugPrint('포트폴리오 업데이트 오류 상세: $e');
      if (e.toString().contains('SocketException') ||
          e.toString().contains('Connection')) {
        throw Exception('서버에 연결할 수 없습니다. 백엔드 서버가 실행 중인지 확인해주세요');
      }
      rethrow;
    }
  }

  // Agent endpoints
  Future<AgentTaskResponse> runAgentWorker() async {
    try {
      debugPrint('에이전트 워커 실행 시도');

      final response = await http.post(
        Uri.parse('$baseUrl/agent/run-worker'),
        headers: _headers,
      );

      debugPrint('에이전트 워커 응답 상태코드: ${response.statusCode}');
      debugPrint('에이전트 워커 응답 body: ${response.body}');

      if (response.statusCode == 200) {
        final body = json.decode(response.body);
        return AgentTaskResponse.fromJson(body);
      } else {
        throw Exception('에이전트 워커를 실행할 수 없습니다 (${response.statusCode})');
      }
    } catch (e) {
      debugPrint('에이전트 워커 실행 오류 상세: $e');
      if (e.toString().contains('SocketException') ||
          e.toString().contains('Connection')) {
        throw Exception('서버에 연결할 수 없습니다. 백엔드 서버가 실행 중인지 확인해주세요');
      }
      rethrow;
    }
  }

  Future<TaskProgress> getTaskProgress(String taskId) async {
    try {
      debugPrint('태스크 진행 상황 조회 시도: $taskId');

      final response = await http.get(
        Uri.parse('$baseUrl/agent/task/$taskId'),
        headers: _headers,
      );

      debugPrint('태스크 진행 상황 응답 상태코드: ${response.statusCode}');
      debugPrint('태스크 진행 상황 응답 body: ${response.body}');

      if (response.statusCode == 200) {
        final body = json.decode(response.body);
        return TaskProgress.fromJson(body);
      } else {
        throw Exception('태스크 진행 상황을 조회할 수 없습니다 (${response.statusCode})');
      }
    } catch (e) {
      debugPrint('태스크 진행 상황 조회 오류 상세: $e');
      if (e.toString().contains('SocketException') ||
          e.toString().contains('Connection')) {
        throw Exception('서버에 연결할 수 없습니다. 백엔드 서버가 실행 중인지 확인해주세요');
      }
      rethrow;
    }
  }

  Future<void> cancelTask(String taskId) async {
    try {
      debugPrint('태스크 취소 시도: $taskId');

      final response = await http.delete(
        Uri.parse('$baseUrl/agent/task/$taskId'),
        headers: _headers,
      );

      debugPrint('태스크 취소 응답 상태코드: ${response.statusCode}');
      debugPrint('태스크 취소 응답 body: ${response.body}');

      if (response.statusCode == 200) {
        final body = json.decode(response.body);
        debugPrint('태스크 취소 성공: ${body['message']}');
      } else if (response.statusCode == 404) {
        throw Exception('태스크를 찾을 수 없습니다');
      } else {
        throw Exception('태스크를 취소할 수 없습니다 (${response.statusCode})');
      }
    } catch (e) {
      debugPrint('태스크 취소 오류 상세: $e');
      if (e.toString().contains('SocketException') ||
          e.toString().contains('Connection')) {
        throw Exception('서버에 연결할 수 없습니다. 백엔드 서버가 실행 중인지 확인해주세요');
      }
      rethrow;
    }
  }

  // Backend에서는 에이전트 상태 조회 엔드포인트가 없으므로
  // 프론트엔드에서 간단히 처리
  Future<AgentStatus> getAgentStatus() async {
    // 실제 구현에서는 다른 방식으로 상태를 확인해야 함
    return AgentStatus(
      status: AgentStatusType.completed,
      progress: 100.0,
      result: {
        'summary': '에이전트 실행이 완료되었습니다.',
        'timestamp': DateTime.now().toIso8601String(),
      },
    );
  }

  // Position endpoints
  Future<Position> getPosition(int positionId) async {
    try {
      debugPrint('포지션 조회 시도: $positionId');

      final response = await http.get(
        Uri.parse('$baseUrl/position/$positionId'),
        headers: _headers,
      );

      debugPrint('포지션 응답 상태코드: ${response.statusCode}');
      debugPrint('포지션 응답 body: ${response.body}');

      if (response.statusCode == 200) {
        final data = json.decode(response.body);
        return Position.fromJson(data);
      } else {
        throw Exception('포지션을 조회할 수 없습니다 (${response.statusCode})');
      }
    } catch (e) {
      debugPrint('포지션 조회 오류 상세: $e');
      if (e.toString().contains('SocketException') ||
          e.toString().contains('Connection')) {
        throw Exception('서버에 연결할 수 없습니다. 백엔드 서버가 실행 중인지 확인해주세요');
      }
      rethrow;
    }
  }

  Future<Position> createPosition(Map<String, dynamic> positionData) async {
    try {
      debugPrint('포지션 생성 시도: $positionData');

      final response = await http.post(
        Uri.parse('$baseUrl/position/'),
        headers: _headers,
        body: json.encode(positionData),
      );

      debugPrint('포지션 생성 응답 상태코드: ${response.statusCode}');
      debugPrint('포지션 생성 응답 body: ${response.body}');

      if (response.statusCode == 200) {
        final data = json.decode(response.body);
        return Position.fromJson(data);
      } else {
        throw Exception('포지션을 생성할 수 없습니다 (${response.statusCode})');
      }
    } catch (e) {
      debugPrint('포지션 생성 오류 상세: $e');
      if (e.toString().contains('SocketException') ||
          e.toString().contains('Connection')) {
        throw Exception('서버에 연결할 수 없습니다. 백엔드 서버가 실행 중인지 확인해주세요');
      }
      rethrow;
    }
  }

  Future<Position> updatePosition(
    int positionId,
    Map<String, dynamic> updates,
  ) async {
    try {
      debugPrint('포지션 업데이트 시도: $positionId, $updates');

      final response = await http.patch(
        Uri.parse('$baseUrl/position/$positionId'),
        headers: _headers,
        body: json.encode(updates),
      );

      debugPrint('포지션 업데이트 응답 상태코드: ${response.statusCode}');
      debugPrint('포지션 업데이트 응답 body: ${response.body}');

      if (response.statusCode == 200) {
        final data = json.decode(response.body);
        return Position.fromJson(data);
      } else {
        throw Exception('포지션을 업데이트할 수 없습니다 (${response.statusCode})');
      }
    } catch (e) {
      debugPrint('포지션 업데이트 오류 상세: $e');
      if (e.toString().contains('SocketException') ||
          e.toString().contains('Connection')) {
        throw Exception('서버에 연결할 수 없습니다. 백엔드 서버가 실행 중인지 확인해주세요');
      }
      rethrow;
    }
  }

  Future<Position> deletePosition(int positionId) async {
    try {
      debugPrint('포지션 삭제 시도: $positionId');

      final response = await http.delete(
        Uri.parse('$baseUrl/position/$positionId'),
        headers: _headers,
      );

      debugPrint('포지션 삭제 응답 상태코드: ${response.statusCode}');
      debugPrint('포지션 삭제 응답 body: ${response.body}');

      if (response.statusCode == 200) {
        final data = json.decode(response.body);
        return Position.fromJson(data);
      } else {
        throw Exception('포지션을 삭제할 수 없습니다 (${response.statusCode})');
      }
    } catch (e) {
      debugPrint('포지션 삭제 오류 상세: $e');
      if (e.toString().contains('SocketException') ||
          e.toString().contains('Connection')) {
        throw Exception('서버에 연결할 수 없습니다. 백엔드 서버가 실행 중인지 확인해주세요');
      }
      rethrow;
    }
  }

  // Health endpoints
  Future<Map<String, dynamic>> getHealth() async {
    try {
      debugPrint('헬스체크 시도');

      final response = await http.get(
        Uri.parse('$baseUrl/health'),
        headers: _headers,
      );

      debugPrint('헬스체크 응답 상태코드: ${response.statusCode}');
      debugPrint('헬스체크 응답 body: ${response.body}');

      if (response.statusCode == 200) {
        return json.decode(response.body);
      } else {
        throw Exception('헬스체크 실패 (${response.statusCode})');
      }
    } catch (e) {
      debugPrint('헬스체크 오류 상세: $e');
      if (e.toString().contains('SocketException') ||
          e.toString().contains('Connection')) {
        throw Exception('서버에 연결할 수 없습니다. 백엔드 서버가 실행 중인지 확인해주세요');
      }
      rethrow;
    }
  }

  Future<Map<String, dynamic>> getHealthDb() async {
    try {
      debugPrint('DB 헬스체크 시도');

      final response = await http.get(
        Uri.parse('$baseUrl/health/db'),
        headers: _headers,
      );

      debugPrint('DB 헬스체크 응답 상태코드: ${response.statusCode}');
      debugPrint('DB 헬스체크 응답 body: ${response.body}');

      if (response.statusCode == 200) {
        return json.decode(response.body);
      } else {
        throw Exception('DB 헬스체크 실패 (${response.statusCode})');
      }
    } catch (e) {
      debugPrint('DB 헬스체크 오류 상세: $e');
      if (e.toString().contains('SocketException') ||
          e.toString().contains('Connection')) {
        throw Exception('서버에 연결할 수 없습니다. 백엔드 서버가 실행 중인지 확인해주세요');
      }
      rethrow;
    }
  }

  // Auth signout endpoint
  Future<Map<String, dynamic>> signout() async {
    try {
      debugPrint('로그아웃 시도');

      final response = await http.post(
        Uri.parse('$baseUrl/auth/signout'),
        headers: _headers,
      );

      debugPrint('로그아웃 응답 상태코드: ${response.statusCode}');
      debugPrint('로그아웃 응답 body: ${response.body}');

      if (response.statusCode == 200) {
        return json.decode(response.body);
      } else {
        throw Exception('로그아웃 실패 (${response.statusCode})');
      }
    } catch (e) {
      debugPrint('로그아웃 오류 상세: $e');
      if (e.toString().contains('SocketException') ||
          e.toString().contains('Connection')) {
        throw Exception('서버에 연결할 수 없습니다. 백엔드 서버가 실행 중인지 확인해주세요');
      }
      rethrow;
    }
  }

  // Current user delete endpoint (회원 탈퇴)
  Future<void> deleteCurrentUser() async {
    try {
      debugPrint('현재 사용자 탈퇴 시도');
      debugPrint('현재 토큰: $_authToken');
      debugPrint('요청 헤더: $_headers');

      final response = await http.delete(
        Uri.parse('$baseUrl/users/me'),
        headers: _headers,
      );

      debugPrint('사용자 탈퇴 응답 상태코드: ${response.statusCode}');

      if (response.statusCode == 204) {
        // 성공적으로 삭제됨 (No Content)
        debugPrint('사용자 탈퇴 성공');
        return;
      } else if (response.statusCode == 401 || response.statusCode == 422) {
        throw Exception('로그인이 필요합니다');
      } else {
        debugPrint('사용자 탈퇴 실패: ${response.statusCode} - ${response.body}');
        throw Exception('사용자 탈퇴 실패 (${response.statusCode})');
      }
    } catch (e) {
      debugPrint('사용자 탈퇴 오류 상세: $e');
      if (e.toString().contains('SocketException') ||
          e.toString().contains('Connection')) {
        throw Exception('서버에 연결할 수 없습니다. 백엔드 서버가 실행 중인지 확인해주세요');
      }
      rethrow;
    }
  }

  Future<void> resendVerificationEmail(String email) async {
    try {
      debugPrint('이메일 재발송 시도: $email');

      final response = await http.post(
        Uri.parse('$baseUrl/auth/resend-verification-email'),
        headers: {'Content-Type': 'application/x-www-form-urlencoded'},
        body: {'email': email},
      );

      debugPrint('이메일 재발송 응답 상태코드: ${response.statusCode}');
      debugPrint('이메일 재발송 응답 body: ${response.body}');

      if (response.statusCode == 200) {
        debugPrint('이메일 재발송 성공');
      } else {
        final errorMessage = response.statusCode == 400
            ? '유효하지 않은 이메일입니다'
            : '서버 오류가 발생했습니다 (${response.statusCode})';
        throw Exception(errorMessage);
      }
    } catch (e) {
      debugPrint('이메일 재발송 오류 상세: $e');
      if (e.toString().contains('SocketException') ||
          e.toString().contains('Connection')) {
        throw Exception('서버에 연결할 수 없습니다. 백엔드 서버가 실행 중인지 확인해주세요');
      }
      rethrow;
    }
  }

  // Stock search endpoint
  Future<List<StockSearchResult>> searchStock(String query) async {
    try {
      debugPrint('종목 검색 시도: $query');

      final response = await http.get(
        Uri.parse('$baseUrl/stock/search?query=${Uri.encodeComponent(query)}'),
        headers: _headers,
      );

      debugPrint('종목 검색 응답 상태코드: ${response.statusCode}');
      debugPrint('종목 검색 응답 body: ${response.body}');

      if (response.statusCode == 200) {
        final List<dynamic> data = json.decode(response.body);
        return data.map((item) => StockSearchResult.fromJson(item)).toList();
      } else {
        throw Exception('종목 검색 실패 (${response.statusCode})');
      }
    } catch (e) {
      debugPrint('종목 검색 오류 상세: $e');
      if (e.toString().contains('SocketException') ||
          e.toString().contains('Connection')) {
        throw Exception('서버에 연결할 수 없습니다. 백엔드 서버가 실행 중인지 확인해주세요');
      }
      rethrow;
    }
  }
}
