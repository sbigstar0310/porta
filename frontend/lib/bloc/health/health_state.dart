import 'package:equatable/equatable.dart';

abstract class HealthState extends Equatable {
  const HealthState();

  @override
  List<Object?> get props => [];
}

class HealthInitial extends HealthState {}

class HealthLoading extends HealthState {}

class HealthSuccess extends HealthState {
  final Map<String, dynamic> healthData;
  final Map<String, dynamic>? dbHealthData;

  const HealthSuccess({required this.healthData, this.dbHealthData});

  @override
  List<Object?> get props => [healthData, dbHealthData];
}

class HealthError extends HealthState {
  final String message;

  const HealthError(this.message);

  @override
  List<Object?> get props => [message];
}
