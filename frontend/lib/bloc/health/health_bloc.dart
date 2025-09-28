import 'package:flutter_bloc/flutter_bloc.dart';
import '../../services/api_service.dart';
import 'health_event.dart';
import 'health_state.dart';

class HealthBloc extends Bloc<HealthEvent, HealthState> {
  final ApiService _apiService = ApiService();

  HealthBloc() : super(HealthInitial()) {
    on<HealthCheckRequested>(_onHealthCheckRequested);
    on<HealthDbCheckRequested>(_onHealthDbCheckRequested);
    on<HealthReset>(_onHealthReset);
  }

  Future<void> _onHealthCheckRequested(
    HealthCheckRequested event,
    Emitter<HealthState> emit,
  ) async {
    emit(HealthLoading());

    try {
      final healthData = await _apiService.getHealth();
      final dbHealthData = await _apiService.getHealthDb();

      emit(HealthSuccess(healthData: healthData, dbHealthData: dbHealthData));
    } catch (e) {
      emit(HealthError('헬스체크에 실패했습니다: $e'));
    }
  }

  Future<void> _onHealthDbCheckRequested(
    HealthDbCheckRequested event,
    Emitter<HealthState> emit,
  ) async {
    emit(HealthLoading());

    try {
      final dbHealthData = await _apiService.getHealthDb();

      // 현재 state가 HealthSuccess인 경우 기존 healthData 유지
      if (state is HealthSuccess) {
        final currentState = state as HealthSuccess;
        emit(
          HealthSuccess(
            healthData: currentState.healthData,
            dbHealthData: dbHealthData,
          ),
        );
      } else {
        emit(
          HealthSuccess(
            healthData: {'status': 'unknown'},
            dbHealthData: dbHealthData,
          ),
        );
      }
    } catch (e) {
      emit(HealthError('DB 헬스체크에 실패했습니다: $e'));
    }
  }

  void _onHealthReset(HealthReset event, Emitter<HealthState> emit) {
    emit(HealthInitial());
  }
}
