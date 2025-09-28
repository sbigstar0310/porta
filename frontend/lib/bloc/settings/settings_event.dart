import 'package:equatable/equatable.dart';

abstract class SettingsEvent extends Equatable {
  const SettingsEvent();

  @override
  List<Object?> get props => [];
}

class SettingsLoadRequested extends SettingsEvent {}

class SettingsNotificationsToggled extends SettingsEvent {
  final bool enabled;

  const SettingsNotificationsToggled(this.enabled);

  @override
  List<Object> get props => [enabled];
}

class SettingsDarkModeToggled extends SettingsEvent {
  final bool enabled;

  const SettingsDarkModeToggled(this.enabled);

  @override
  List<Object> get props => [enabled];
}

class SettingsReportTimeUpdated extends SettingsEvent {
  final String time;

  const SettingsReportTimeUpdated(this.time);

  @override
  List<Object> get props => [time];
}

class SettingsWeekendReportsToggled extends SettingsEvent {
  final bool enabled;

  const SettingsWeekendReportsToggled(this.enabled);

  @override
  List<Object> get props => [enabled];
}

class SettingsLanguageChanged extends SettingsEvent {
  final String language;

  const SettingsLanguageChanged(this.language);

  @override
  List<Object> get props => [language];
}

class SettingsResetToDefaults extends SettingsEvent {}
