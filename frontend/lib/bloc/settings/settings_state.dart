import 'package:equatable/equatable.dart';
import '../../models/settings.dart';

abstract class SettingsState extends Equatable {
  const SettingsState();

  @override
  List<Object?> get props => [];
}

class SettingsInitial extends SettingsState {}

class SettingsLoading extends SettingsState {}

class SettingsLoadedState extends SettingsState {
  final AppSettings settings;

  const SettingsLoadedState(this.settings);

  List<String> get availableLanguages => ['ko', 'en'];

  String getLanguageName(String code) {
    switch (code) {
      case 'ko':
        return '한국어';
      case 'en':
        return 'English';
      default:
        return code;
    }
  }

  @override
  List<Object> get props => [settings];

  SettingsLoadedState copyWith({AppSettings? settings}) {
    return SettingsLoadedState(settings ?? this.settings);
  }
}

class SettingsError extends SettingsState {
  final String message;

  const SettingsError(this.message);

  @override
  List<Object> get props => [message];
}
