import 'package:equatable/equatable.dart';

abstract class AgentEvent extends Equatable {
  const AgentEvent();

  @override
  List<Object?> get props => [];
}

class AgentRunRequested extends AgentEvent {}

class AgentTaskCancelRequested extends AgentEvent {
  final String taskId;

  const AgentTaskCancelRequested(this.taskId);

  @override
  List<Object> get props => [taskId];
}

class AgentTaskProgressRequested extends AgentEvent {
  final String taskId;

  const AgentTaskProgressRequested(this.taskId);

  @override
  List<Object> get props => [taskId];
}

class AgentTaskStarted extends AgentEvent {
  final String taskId;
  final String message;

  const AgentTaskStarted({required this.taskId, required this.message});

  @override
  List<Object> get props => [taskId, message];
}

class AgentTaskProgressUpdated extends AgentEvent {
  final String taskId;
  final double progress;
  final String? message;

  const AgentTaskProgressUpdated({
    required this.taskId,
    required this.progress,
    this.message,
  });

  @override
  List<Object?> get props => [taskId, progress, message];
}

class AgentTaskCompleted extends AgentEvent {
  final String taskId;
  final Map<String, dynamic>? result;

  const AgentTaskCompleted({required this.taskId, this.result});

  @override
  List<Object?> get props => [taskId, result];
}

class AgentTaskFailed extends AgentEvent {
  final String taskId;
  final String error;

  const AgentTaskFailed({required this.taskId, required this.error});

  @override
  List<Object> get props => [taskId, error];
}

class AgentTaskCancelled extends AgentEvent {
  final String taskId;

  const AgentTaskCancelled(this.taskId);

  @override
  List<Object> get props => [taskId];
}

class AgentReset extends AgentEvent {}
