enum AgentStatusType { idle, running, completed, error }

class AgentStatus {
  final AgentStatusType status;
  final String? currentTask;
  final double progress;
  final String? error;
  final DateTime? startTime;
  final DateTime? endTime;
  final Map<String, dynamic>? result;

  AgentStatus({
    required this.status,
    this.currentTask,
    this.progress = 0.0,
    this.error,
    this.startTime,
    this.endTime,
    this.result,
  });

  factory AgentStatus.fromJson(Map<String, dynamic> json) {
    return AgentStatus(
      status: AgentStatusType.values.firstWhere(
        (e) => e.name == json['status'],
        orElse: () => AgentStatusType.idle,
      ),
      currentTask: json['current_task'] as String?,
      progress: (json['progress'] as num?)?.toDouble() ?? 0.0,
      error: json['error'] as String?,
      startTime: json['start_time'] != null
          ? DateTime.parse(json['start_time'] as String)
          : null,
      endTime: json['end_time'] != null
          ? DateTime.parse(json['end_time'] as String)
          : null,
      result: json['result'] as Map<String, dynamic>?,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'status': status.name,
      'current_task': currentTask,
      'progress': progress,
      'error': error,
      'start_time': startTime?.toIso8601String(),
      'end_time': endTime?.toIso8601String(),
      'result': result,
    };
  }

  AgentStatus copyWith({
    AgentStatusType? status,
    String? currentTask,
    double? progress,
    String? error,
    DateTime? startTime,
    DateTime? endTime,
    Map<String, dynamic>? result,
  }) {
    return AgentStatus(
      status: status ?? this.status,
      currentTask: currentTask ?? this.currentTask,
      progress: progress ?? this.progress,
      error: error ?? this.error,
      startTime: startTime ?? this.startTime,
      endTime: endTime ?? this.endTime,
      result: result ?? this.result,
    );
  }
}
