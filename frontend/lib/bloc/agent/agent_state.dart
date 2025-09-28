import 'package:equatable/equatable.dart';

abstract class AgentState extends Equatable {
  const AgentState();

  @override
  List<Object?> get props => [];
}

class AgentInitial extends AgentState {}

class AgentLoading extends AgentState {}

class AgentIdle extends AgentState {}

class AgentRunning extends AgentState {
  final String taskId;
  final double progress;
  final String? currentTask;
  final DateTime? startTime;

  const AgentRunning({
    required this.taskId,
    required this.progress,
    this.currentTask,
    this.startTime,
  });

  bool get isRunning => true;
  bool get canCancel => true;

  Duration? get elapsedTime {
    if (startTime == null) return null;
    return DateTime.now().difference(startTime!);
  }

  String get statusMessage => currentTask ?? '실행 중...';

  @override
  List<Object?> get props => [taskId, progress, currentTask, startTime];

  AgentRunning copyWith({
    String? taskId,
    double? progress,
    String? currentTask,
    DateTime? startTime,
  }) {
    return AgentRunning(
      taskId: taskId ?? this.taskId,
      progress: progress ?? this.progress,
      currentTask: currentTask ?? this.currentTask,
      startTime: startTime ?? this.startTime,
    );
  }
}

class AgentCompleted extends AgentState {
  final String taskId;
  final DateTime? startTime;
  final DateTime endTime;
  final Map<String, dynamic>? result;

  const AgentCompleted({
    required this.taskId,
    this.startTime,
    required this.endTime,
    this.result,
  });

  Duration? get elapsedTime {
    if (startTime == null) return null;
    return endTime.difference(startTime!);
  }

  String get statusMessage => '완료됨';

  String? get reportMd {
    if (result != null && result!['result'] is Map<String, dynamic>) {
      final resultData = result!['result'] as Map<String, dynamic>;
      if (resultData['report_md'] is String) {
        return resultData['report_md'] as String;
      }
    }
    return null;
  }

  @override
  List<Object?> get props => [taskId, startTime, endTime, result];
}

class AgentCancelled extends AgentState {
  final String taskId;
  final DateTime? startTime;
  final DateTime endTime;

  const AgentCancelled({
    required this.taskId,
    this.startTime,
    required this.endTime,
  });

  Duration? get elapsedTime {
    if (startTime == null) return null;
    return endTime.difference(startTime!);
  }

  String get statusMessage => '취소됨';

  @override
  List<Object?> get props => [taskId, startTime, endTime];
}

class AgentError extends AgentState {
  final String taskId;
  final String message;
  final DateTime? startTime;
  final DateTime endTime;

  const AgentError({
    required this.taskId,
    required this.message,
    this.startTime,
    required this.endTime,
  });

  Duration? get elapsedTime {
    if (startTime == null) return null;
    return endTime.difference(startTime!);
  }

  String get statusMessage => '오류 발생';

  @override
  List<Object?> get props => [taskId, message, startTime, endTime];
}
