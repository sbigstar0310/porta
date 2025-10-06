import 'dart:convert';
import '../models/user.dart';
import '../models/portfolio.dart';
import '../models/stock_search_result.dart';
import '../models/task_progress.dart';
import '../models/schedule.dart';
import 'storage_service.dart';
import 'dio_client.dart';

class ApiService {
  // 싱글톤 패턴 구현
  static final ApiService _instance = ApiService._internal();
  factory ApiService() => _instance;
  ApiService._internal();

  final DioClient _dioClient = DioClient();

  void setAuthToken(String token) {
    // DioClient의 인터셉터에서 자동으로 토큰을 처리하므로 저장만 함
    StorageService.saveAuthToken(token);
  }

  /// 토큰 갱신 시도
  Future<bool> refreshToken() async {
    return await _dioClient.refreshTokenManually();
  }

  // Auth endpoints
  Future<User> login(String email, String password) async {
    final response = await _dioClient.postForm(
      '/auth/login',
      data: {'email': email, 'password': password},
    );

    return User.fromJson(response.data);
  }

  Future<User> register(String email, String password, String? name) async {
    final requestBody = {
      'email': email,
      'password': password,
      'timezone': 'Asia/Seoul',
      'language': 'ko',
    };

    final response = await _dioClient.post('/users', data: requestBody);

    return User.fromJson(response.data);
  }

  Future<User> getCurrentUser() async {
    final token = await StorageService.getAuthToken();
    if (token != null && token.isNotEmpty && token != 'dummy_token') {
      final userData = await StorageService.getUserData();
      if (userData != null) {
        return User.fromJson(json.decode(userData));
      }
    }
    throw Exception('현재 사용자 정보를 찾을 수 없습니다');
  }

  Future<User> refreshSession(String refreshToken) async {
    final response = await _dioClient.postForm(
      '/auth/refresh',
      data: {'refresh_token': refreshToken},
    );
    return User.fromJson(response.data);
  }

  // Portfolio endpoints
  Future<Portfolio> getPortfolio() async {
    final response = await _dioClient.get('/portfolio');
    return Portfolio.fromJson(response.data);
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
    final response = await _dioClient.patch('/portfolio', data: updates);
    return Portfolio.fromJson(response.data);
  }

  // Agent endpoints
  Future<AgentTaskResponse> runAgentWorker() async {
    final response = await _dioClient.post('/agent/run-worker');
    return AgentTaskResponse.fromJson(response.data);
  }

  Future<TaskProgress> getTaskProgress(String taskId) async {
    final response = await _dioClient.get('/agent/task/$taskId');
    return TaskProgress.fromJson(response.data);
  }

  Future<void> cancelTask(String taskId) async {
    await _dioClient.delete('/agent/task/$taskId');
  }

  // Position endpoints
  Future<Position> getPosition(int positionId) async {
    final response = await _dioClient.get('/position/$positionId');
    return Position.fromJson(response.data);
  }

  Future<Position> createPosition(Map<String, dynamic> positionData) async {
    final response = await _dioClient.post('/position/', data: positionData);
    return Position.fromJson(response.data);
  }

  Future<Position> updatePosition(
    int positionId,
    Map<String, dynamic> updates,
  ) async {
    final response = await _dioClient.patch(
      '/position/$positionId',
      data: updates,
    );
    return Position.fromJson(response.data);
  }

  Future<Map<String, dynamic>> deletePosition(int positionId) async {
    final response = await _dioClient.delete('/position/$positionId');
    return response.data;
  }

  // Health endpoints
  Future<Map<String, dynamic>> getHealth() async {
    final response = await _dioClient.get('/health');
    return response.data;
  }

  Future<Map<String, dynamic>> getHealthDb() async {
    final response = await _dioClient.get('/health/db');
    return response.data;
  }

  // Auth signout endpoint
  Future<Map<String, dynamic>> signout() async {
    final response = await _dioClient.post('/auth/signout');
    return response.data;
  }

  // Current user delete endpoint (회원 탈퇴)
  Future<void> deleteCurrentUser() async {
    await _dioClient.delete('/users/me');
  }

  Future<void> resendVerificationEmail(String email) async {
    await _dioClient.postForm(
      '/auth/resend-verification-email',
      data: {'email': email},
    );
  }

  // Stock search endpoint
  Future<List<StockSearchResult>> searchStock(String query) async {
    final response = await _dioClient.get(
      '/stock/search',
      queryParameters: {'query': query},
    );

    final List<dynamic> data = response.data;
    return data.map((item) => StockSearchResult.fromJson(item)).toList();
  }

  // Schedule endpoints
  /// 현재 사용자의 스케줄 조회 (없으면 null 반환)
  Future<Schedule?> getMySchedule() async {
    final response = await _dioClient.get('/schedules/me');
    final data = response.data;

    // null 체크 - 스케줄이 없을 수 있음
    if (data == null) {
      return null;
    }
    return Schedule.fromJson(data);
  }

  /// 새로운 스케줄 생성
  Future<Schedule> createSchedule({
    required int userId,
    required int hour,
    required int minute,
    String timezone = 'Asia/Seoul',
    bool enabled = true,
  }) async {
    final requestBody = {
      'user_id': userId,
      'hour': hour,
      'minute': minute,
      'timezone': timezone,
      'enabled': enabled,
    };

    final response = await _dioClient.post('/schedules', data: requestBody);
    return Schedule.fromJson(response.data);
  }

  /// 현재 사용자의 스케줄 업데이트
  Future<Schedule> updateMySchedule({
    int? hour,
    int? minute,
    String? timezone,
    bool? enabled,
  }) async {
    final requestBody = <String, dynamic>{};
    if (hour != null) requestBody['hour'] = hour;
    if (minute != null) requestBody['minute'] = minute;
    if (timezone != null) requestBody['timezone'] = timezone;
    if (enabled != null) requestBody['enabled'] = enabled;

    final response = await _dioClient.patch('/schedules/me', data: requestBody);
    return Schedule.fromJson(response.data);
  }
}
