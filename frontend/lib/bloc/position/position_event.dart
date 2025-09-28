abstract class PositionEvent {}

class PositionLoadRequested extends PositionEvent {
  final int positionId;

  PositionLoadRequested({required this.positionId});
}

class PositionCreateRequested extends PositionEvent {
  final Map<String, dynamic> positionData;

  PositionCreateRequested({required this.positionData});
}

class PositionUpdateRequested extends PositionEvent {
  final int positionId;
  final Map<String, dynamic> updates;

  PositionUpdateRequested({required this.positionId, required this.updates});
}

class PositionDeleteRequested extends PositionEvent {
  final int positionId;

  PositionDeleteRequested({required this.positionId});
}

class PositionReset extends PositionEvent {}
