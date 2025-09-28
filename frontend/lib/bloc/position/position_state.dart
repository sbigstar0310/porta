import 'package:equatable/equatable.dart';
import '../../models/portfolio.dart';

abstract class PositionState extends Equatable {
  const PositionState();

  @override
  List<Object?> get props => [];
}

class PositionInitial extends PositionState {}

class PositionLoading extends PositionState {}

class PositionLoaded extends PositionState {
  final Position position;

  const PositionLoaded({required this.position});

  @override
  List<Object?> get props => [position];
}

class PositionError extends PositionState {
  final String message;

  const PositionError(this.message);

  @override
  List<Object?> get props => [message];
}

class PositionSuccess extends PositionState {
  final String message;
  final Position? position;

  const PositionSuccess({required this.message, this.position});

  @override
  List<Object?> get props => [message, position];
}
