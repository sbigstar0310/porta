import 'dart:convert';
import 'package:flutter_bloc/flutter_bloc.dart';
import '../../models/settings.dart';
import '../../models/user.dart';
import '../../services/storage_service.dart';
import '../../services/api_service.dart';
import 'settings_event.dart';
import 'settings_state.dart';

class SettingsBloc extends Bloc<SettingsEvent, SettingsState> {
  final ApiService _apiService = ApiService();

  SettingsBloc() : super(SettingsInitial()) {
    on<SettingsLoadRequested>(_onSettingsLoaded);
    on<SettingsDarkModeToggled>(_onDarkModeToggled);
    on<SettingsReportTimeUpdated>(_onReportTimeUpdated);
    on<SettingsLanguageChanged>(_onLanguageChanged);
    on<SettingsResetToDefaults>(_onResetToDefaults);
  }

  Future<void> _onSettingsLoaded(
    SettingsLoadRequested event,
    Emitter<SettingsState> emit,
  ) async {
    emit(SettingsLoading());

    try {
      final settings = await StorageService.getSettings();

      // 백엔드에서 스케줄을 가져와서 로컬 설정과 동기화
      try {
        final schedule = await _apiService.getMySchedule();
        print('백엔드 스케줄: $schedule');
        if (schedule != null) {
          // 백엔드 스케줄이 있으면 로컬 설정에 반영
          final syncedSettings = settings.copyWith(
            reportTime: schedule.timeString,
          );

          // 로컬 설정과 백엔드가 다른 경우에만 저장
          if (settings.reportTime != schedule.timeString) {
            await StorageService.saveSettings(syncedSettings);
          }

          emit(SettingsLoadedState(syncedSettings));
          return;
        } else {
          // 백엔드에 스케줄이 없는 경우, 사용자가 직접 설정할 때까지 기다림
          print('백엔드에 스케줄이 없음 - 사용자가 직접 설정할 때까지 대기');
        }
      } catch (e) {
        // 백엔드 조회 실패 시 로컬 설정 사용
        print('백엔드 스케줄 조회 실패 (로컬 설정 사용): $e');
      }

      emit(SettingsLoadedState(settings));
    } catch (e) {
      emit(SettingsError('설정 로딩 실패: $e'));
    }
  }

  Future<void> _onDarkModeToggled(
    SettingsDarkModeToggled event,
    Emitter<SettingsState> emit,
  ) async {
    await _updateSettings(
      emit,
      (settings) => settings.copyWith(darkModeEnabled: event.enabled),
    );
  }

  Future<void> _onReportTimeUpdated(
    SettingsReportTimeUpdated event,
    Emitter<SettingsState> emit,
  ) async {
    // Validate time format (HH:mm)
    if (!RegExp(r'^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$').hasMatch(event.time)) {
      emit(const SettingsError('잘못된 시간 형식입니다. HH:mm 형식으로 입력해주세요.'));
      return;
    }

    final currentState = state;
    if (currentState is! SettingsLoadedState) return;

    try {
      // 시간을 hour와 minute로 분리
      final timeParts = event.time.split(':');
      final hour = int.parse(timeParts[0]);
      final minute = int.parse(timeParts[1]);

      // 1. 먼저 UI를 즉시 업데이트 (사용자 경험 개선)
      final immediateSettings = currentState.settings.copyWith(
        reportTime: event.time,
      );
      await StorageService.saveSettings(immediateSettings);
      emit(SettingsLoadedState(immediateSettings));

      // 2. 백그라운드에서 백엔드 동기화 처리
      String finalReportTime = event.time; // 기본값은 요청한 시간

      try {
        // 먼저 기존 스케줄이 있는지 확인
        final existingSchedule = await _apiService.getMySchedule();

        if (existingSchedule != null) {
          // 스케줄이 있으면 업데이트
          final updatedSchedule = await _apiService.updateMySchedule(
            hour: hour,
            minute: minute,
          );
          finalReportTime = updatedSchedule.timeString; // 실제 업데이트된 시간 사용
        } else {
          // 스케줄이 없으면 생성
          // 사용자 정보에서 user_id 가져오기
          final userDataJson = await StorageService.getUserData();
          if (userDataJson != null && userDataJson.isNotEmpty) {
            try {
              final userMap = json.decode(userDataJson) as Map<String, dynamic>;
              final user = User.fromJson(userMap);

              final createdSchedule = await _apiService.createSchedule(
                userId: user.id,
                hour: hour,
                minute: minute,
              );
              finalReportTime = createdSchedule.timeString; // 실제 생성된 시간 사용
            } catch (parseError) {
              print('사용자 데이터 파싱 실패: $parseError');
              // 파싱 실패 시 스케줄 생성을 건너뛰고 로컬 저장만 진행
            }
          } else {
            print('사용자 데이터가 없어 스케줄 생성을 건너뜁니다.');
          }
        }

        // 3. 백엔드 동기화 완료 후 실제 값이 다르면 다시 업데이트
        if (finalReportTime != event.time) {
          final finalSettings = currentState.settings.copyWith(
            reportTime: finalReportTime,
          );
          await StorageService.saveSettings(finalSettings);
          emit(SettingsLoadedState(finalSettings));
          print('백엔드 동기화 완료: $event.time -> $finalReportTime');
        }
      } catch (e) {
        // 백엔드 업데이트 실패 시 로그만 출력 (UI는 이미 업데이트됨)
        print('백엔드 스케줄 업데이트 실패: $e');
        // 백엔드 실패 시에도 최신 상태를 확인해보기
        try {
          final currentSchedule = await _apiService.getMySchedule();
          if (currentSchedule != null &&
              currentSchedule.timeString != event.time) {
            finalReportTime = currentSchedule.timeString;
            final correctedSettings = currentState.settings.copyWith(
              reportTime: finalReportTime,
            );
            await StorageService.saveSettings(correctedSettings);
            emit(SettingsLoadedState(correctedSettings));
            print('백엔드에서 현재 스케줄로 수정: $event.time -> $finalReportTime');
          }
        } catch (fetchError) {
          print('백엔드 스케줄 조회도 실패: $fetchError');
        }
      }
    } catch (e) {
      emit(SettingsError('설정 업데이트 실패: $e'));
    }
  }

  Future<void> _onLanguageChanged(
    SettingsLanguageChanged event,
    Emitter<SettingsState> emit,
  ) async {
    await _updateSettings(
      emit,
      (settings) => settings.copyWith(language: event.language),
    );
  }

  Future<void> _onResetToDefaults(
    SettingsResetToDefaults event,
    Emitter<SettingsState> emit,
  ) async {
    try {
      final defaultSettings = AppSettings();

      // 백엔드 스케줄 삭제 시도 (사용자가 다시 설정하도록)
      try {
        final existingSchedule = await _apiService.getMySchedule();
        if (existingSchedule != null) {
          // 스케줄이 있으면 삭제하여 사용자가 새로 설정하도록 함
          // 현재 API에 삭제 기능이 없다면 주석 처리
          // await _apiService.deleteMySchedule();
          print('백엔드 스케줄이 존재하지만 삭제 API가 없어 유지됩니다');
        }
      } catch (e) {
        print('백엔드 스케줄 확인 실패: $e');
      }

      await StorageService.saveSettings(defaultSettings);
      emit(SettingsLoadedState(defaultSettings));
    } catch (e) {
      emit(SettingsError('설정 초기화 실패: $e'));
    }
  }

  Future<void> _updateSettings(
    Emitter<SettingsState> emit,
    AppSettings Function(AppSettings) updater,
  ) async {
    final currentState = state;
    if (currentState is! SettingsLoadedState) return;

    try {
      final updatedSettings = updater(currentState.settings);
      await StorageService.saveSettings(updatedSettings);
      emit(SettingsLoadedState(updatedSettings));
    } catch (e) {
      emit(SettingsError('설정 업데이트 실패: $e'));
    }
  }
}
