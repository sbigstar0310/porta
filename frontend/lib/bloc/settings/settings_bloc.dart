import 'package:flutter_bloc/flutter_bloc.dart';
import '../../models/settings.dart';
import '../../services/storage_service.dart';
import 'settings_event.dart';
import 'settings_state.dart';

class SettingsBloc extends Bloc<SettingsEvent, SettingsState> {
  SettingsBloc() : super(SettingsInitial()) {
    on<SettingsLoadRequested>(_onSettingsLoaded);
    on<SettingsNotificationsToggled>(_onNotificationsToggled);
    on<SettingsDarkModeToggled>(_onDarkModeToggled);
    on<SettingsReportTimeUpdated>(_onReportTimeUpdated);
    on<SettingsWeekendReportsToggled>(_onWeekendReportsToggled);
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
      emit(SettingsLoadedState(settings));
    } catch (e) {
      emit(SettingsError('설정 로딩 실패: $e'));
    }
  }

  Future<void> _onNotificationsToggled(
    SettingsNotificationsToggled event,
    Emitter<SettingsState> emit,
  ) async {
    await _updateSettings(
      emit,
      (settings) => settings.copyWith(notificationsEnabled: event.enabled),
    );
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

    await _updateSettings(
      emit,
      (settings) => settings.copyWith(reportTime: event.time),
    );
  }

  Future<void> _onWeekendReportsToggled(
    SettingsWeekendReportsToggled event,
    Emitter<SettingsState> emit,
  ) async {
    await _updateSettings(
      emit,
      (settings) => settings.copyWith(weekendReports: event.enabled),
    );
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
    emit(SettingsLoading());

    try {
      final defaultSettings = AppSettings();
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

    emit(SettingsLoading());

    try {
      final updatedSettings = updater(currentState.settings);
      await StorageService.saveSettings(updatedSettings);
      emit(SettingsLoadedState(updatedSettings));
    } catch (e) {
      emit(SettingsError('설정 업데이트 실패: $e'));
    }
  }
}
