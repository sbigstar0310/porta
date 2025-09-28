import 'package:flutter_bloc/flutter_bloc.dart';
import '../../services/api_service.dart';
import 'position_event.dart';
import 'position_state.dart';

class PositionBloc extends Bloc<PositionEvent, PositionState> {
  final ApiService _apiService = ApiService();

  PositionBloc() : super(PositionInitial()) {
    on<PositionLoadRequested>(_onPositionLoadRequested);
    on<PositionCreateRequested>(_onPositionCreateRequested);
    on<PositionUpdateRequested>(_onPositionUpdateRequested);
    on<PositionDeleteRequested>(_onPositionDeleteRequested);
    on<PositionReset>(_onPositionReset);
  }

  Future<void> _onPositionLoadRequested(
    PositionLoadRequested event,
    Emitter<PositionState> emit,
  ) async {
    emit(PositionLoading());

    try {
      final position = await _apiService.getPosition(event.positionId);
      emit(PositionLoaded(position: position));
    } catch (e) {
      emit(PositionError('포지션을 불러올 수 없습니다: $e'));
    }
  }

  Future<void> _onPositionCreateRequested(
    PositionCreateRequested event,
    Emitter<PositionState> emit,
  ) async {
    emit(PositionLoading());

    try {
      final position = await _apiService.createPosition(event.positionData);
      emit(PositionSuccess(message: '포지션이 성공적으로 생성되었습니다', position: position));
    } catch (e) {
      emit(PositionError('포지션 생성에 실패했습니다: $e'));
    }
  }

  Future<void> _onPositionUpdateRequested(
    PositionUpdateRequested event,
    Emitter<PositionState> emit,
  ) async {
    emit(PositionLoading());

    try {
      final position = await _apiService.updatePosition(
        event.positionId,
        event.updates,
      );
      emit(
        PositionSuccess(message: '포지션이 성공적으로 업데이트되었습니다', position: position),
      );
    } catch (e) {
      emit(PositionError('포지션 업데이트에 실패했습니다: $e'));
    }
  }

  Future<void> _onPositionDeleteRequested(
    PositionDeleteRequested event,
    Emitter<PositionState> emit,
  ) async {
    emit(PositionLoading());

    try {
      await _apiService.deletePosition(event.positionId);
      emit(const PositionSuccess(message: '포지션이 성공적으로 삭제되었습니다'));
    } catch (e) {
      emit(PositionError('포지션 삭제에 실패했습니다: $e'));
    }
  }

  void _onPositionReset(PositionReset event, Emitter<PositionState> emit) {
    emit(PositionInitial());
  }
}
