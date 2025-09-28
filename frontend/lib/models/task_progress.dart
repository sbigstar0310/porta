class TaskProgress {
  final String taskId;
  final String status; // PENDING, PROGRESS, SUCCESS, FAILURE, REVOKED
  final double percent; // 0.0 ~ 100.0
  final String? message;
  final Map<String, dynamic>? result;
  final String? error;

  const TaskProgress({
    required this.taskId,
    required this.status,
    required this.percent,
    this.message,
    this.result,
    this.error,
  });

  factory TaskProgress.fromJson(Map<String, dynamic> json) {
    return TaskProgress(
      taskId: json['task_id'] as String,
      status: json['status'] as String,
      percent: (json['percent'] as num).toDouble(),
      message: json['message'] as String?,
      result: json['result'] as Map<String, dynamic>?,
      error: json['error'] as String?,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'task_id': taskId,
      'status': status,
      'percent': percent,
      'message': message,
      'result': result,
      'error': error,
    };
  }

  bool get isCompleted => status == 'SUCCESS';
  bool get isFailed => status == 'FAILURE';
  bool get isRevoked => status == 'REVOKED';
  bool get isRunning => status == 'PROGRESS' || status == 'STARTED';
  bool get isPending => status == 'PENDING';

  String get displayMessage {
    if (error != null) return error!;
    if (message != null) return message!;

    switch (status) {
      case 'PENDING':
        return '태스크가 대기 중입니다.';
      case 'STARTED':
        return '태스크가 시작되었습니다.';
      case 'PROGRESS':
        return '태스크가 진행 중입니다.';
      case 'SUCCESS':
        return '태스크가 성공적으로 완료되었습니다.';
      case 'FAILURE':
        return '태스크 실행 중 오류가 발생했습니다.';
      case 'REVOKED':
        return '태스크가 취소되었습니다.';
      default:
        return '알 수 없는 태스크 상태: $status';
    }
  }

  @override
  String toString() {
    return 'TaskProgress(taskId: $taskId, status: $status, percent: $percent, message: $message)';
  }
}

class AgentTaskResponse {
  final String message;
  final String taskId;
  final String status; // STARTED, ALREADY_RUNNING

  const AgentTaskResponse({
    required this.message,
    required this.taskId,
    required this.status,
  });

  factory AgentTaskResponse.fromJson(Map<String, dynamic> json) {
    return AgentTaskResponse(
      message: json['message'] as String,
      taskId: json['task_id'] as String,
      status: json['status'] as String,
    );
  }

  Map<String, dynamic> toJson() {
    return {'message': message, 'task_id': taskId, 'status': status};
  }

  bool get isAlreadyRunning => status == 'ALREADY_RUNNING';
  bool get isStarted => status == 'STARTED';

  @override
  String toString() {
    return 'AgentTaskResponse(message: $message, taskId: $taskId, status: $status)';
  }
}
