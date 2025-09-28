import 'dart:async';
import 'package:flutter_bloc/flutter_bloc.dart';
import '../../services/api_service.dart';
import 'agent_event.dart';
import 'agent_state.dart';

class AgentBloc extends Bloc<AgentEvent, AgentState> {
  final ApiService _apiService = ApiService();
  Timer? _pollingTimer;

  AgentBloc() : super(AgentInitial()) {
    on<AgentRunRequested>(_onRunRequested);
    on<AgentTaskCancelRequested>(_onTaskCancelRequested);
    on<AgentTaskProgressRequested>(_onTaskProgressRequested);
    on<AgentTaskStarted>(_onTaskStarted);
    on<AgentTaskProgressUpdated>(_onTaskProgressUpdated);
    on<AgentTaskCompleted>(_onTaskCompleted);
    on<AgentTaskFailed>(_onTaskFailed);
    on<AgentTaskCancelled>(_onTaskCancelled);
    on<AgentReset>(_onReset);
  }

  Future<void> _onRunRequested(
    AgentRunRequested event,
    Emitter<AgentState> emit,
  ) async {
    if (state is AgentRunning) {
      emit(
        AgentError(
          taskId: '',
          message: '에이전트가 이미 실행 중입니다.',
          endTime: DateTime.now(),
        ),
      );
      return;
    }

    emit(AgentLoading());

    try {
      final response = await _apiService.runAgentWorker();

      if (response.isAlreadyRunning) {
        // 이미 실행 중인 태스크가 있는 경우
        add(
          AgentTaskStarted(taskId: response.taskId, message: response.message),
        );
        _startPolling(response.taskId);
      } else if (response.isStarted) {
        // 새로운 태스크가 시작된 경우
        add(
          AgentTaskStarted(taskId: response.taskId, message: response.message),
        );
        _startPolling(response.taskId);
      }
    } catch (e) {
      emit(
        AgentError(
          taskId: '',
          message: '에이전트 실행 실패: $e',
          endTime: DateTime.now(),
        ),
      );
    }
  }

  Future<void> _onTaskStarted(
    AgentTaskStarted event,
    Emitter<AgentState> emit,
  ) async {
    emit(
      AgentRunning(
        taskId: event.taskId,
        progress: 0.0,
        currentTask: event.message,
        startTime: DateTime.now(),
      ),
    );
  }

  Future<void> _onTaskProgressUpdated(
    AgentTaskProgressUpdated event,
    Emitter<AgentState> emit,
  ) async {
    final currentState = state;
    if (currentState is AgentRunning && currentState.taskId == event.taskId) {
      emit(
        currentState.copyWith(
          progress: event.progress,
          currentTask: event.message,
        ),
      );
    }
  }

  Future<void> _onTaskCompleted(
    AgentTaskCompleted event,
    Emitter<AgentState> emit,
  ) async {
    _stopPolling();

    final currentState = state;
    DateTime? startTime;
    if (currentState is AgentRunning) {
      startTime = currentState.startTime;
    }

    emit(
      AgentCompleted(
        taskId: event.taskId,
        startTime: startTime,
        endTime: DateTime.now(),
        result: event.result,
      ),
    );
  }

  Future<void> _onTaskFailed(
    AgentTaskFailed event,
    Emitter<AgentState> emit,
  ) async {
    _stopPolling();

    final currentState = state;
    DateTime? startTime;
    if (currentState is AgentRunning) {
      startTime = currentState.startTime;
    }

    emit(
      AgentError(
        taskId: event.taskId,
        message: event.error,
        startTime: startTime,
        endTime: DateTime.now(),
      ),
    );
  }

  Future<void> _onTaskCancelled(
    AgentTaskCancelled event,
    Emitter<AgentState> emit,
  ) async {
    _stopPolling();

    final currentState = state;
    DateTime? startTime;
    if (currentState is AgentRunning) {
      startTime = currentState.startTime;
    }

    emit(
      AgentCancelled(
        taskId: event.taskId,
        startTime: startTime,
        endTime: DateTime.now(),
      ),
    );
  }

  Future<void> _onTaskCancelRequested(
    AgentTaskCancelRequested event,
    Emitter<AgentState> emit,
  ) async {
    try {
      await _apiService.cancelTask(event.taskId);
      add(AgentTaskCancelled(event.taskId));
    } catch (e) {
      emit(
        AgentError(
          taskId: event.taskId,
          message: '태스크 취소 실패: $e',
          endTime: DateTime.now(),
        ),
      );
    }
  }

  Future<void> _onTaskProgressRequested(
    AgentTaskProgressRequested event,
    Emitter<AgentState> emit,
  ) async {
    try {
      final progress = await _apiService.getTaskProgress(event.taskId);

      if (progress.isCompleted) {
        add(AgentTaskCompleted(taskId: event.taskId, result: progress.result));
      } else if (progress.isFailed) {
        add(
          AgentTaskFailed(
            taskId: event.taskId,
            error: progress.error ?? progress.displayMessage,
          ),
        );
      } else if (progress.isRevoked) {
        add(AgentTaskCancelled(event.taskId));
      } else if (progress.isRunning || progress.isPending) {
        add(
          AgentTaskProgressUpdated(
            taskId: event.taskId,
            progress: progress.percent,
            message: progress.displayMessage,
          ),
        );
      }
    } catch (e) {
      // 네트워크 오류 등은 로깅만 하고 상태는 유지
      // print('Progress check failed: $e');
    }
  }

  void _startPolling(String taskId) {
    _stopPolling();

    // 10초마다 태스크 상태 확인
    _pollingTimer = Timer.periodic(const Duration(seconds: 10), (timer) {
      add(AgentTaskProgressRequested(taskId));
    });
  }

  void _stopPolling() {
    _pollingTimer?.cancel();
    _pollingTimer = null;
  }

  void _onReset(AgentReset event, Emitter<AgentState> emit) {
    _stopPolling();
    emit(AgentIdle());
  }

  @override
  Future<void> close() {
    _stopPolling();
    return super.close();
  }
}
