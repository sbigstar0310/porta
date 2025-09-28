import 'package:equatable/equatable.dart';
import '../../models/portfolio.dart';

abstract class PortfolioEvent extends Equatable {
  const PortfolioEvent();

  @override
  List<Object?> get props => [];
}

class PortfolioLoadRequested extends PortfolioEvent {}

class PortfolioCreated extends PortfolioEvent {
  final String name;

  const PortfolioCreated(this.name);

  @override
  List<Object> get props => [name];
}

class PortfolioUpdated extends PortfolioEvent {
  final int portfolioId;
  final Map<String, dynamic> updates;

  const PortfolioUpdated({required this.portfolioId, required this.updates});

  @override
  List<Object> get props => [portfolioId, updates];
}

class PortfolioSelected extends PortfolioEvent {
  final Portfolio portfolio;

  const PortfolioSelected(this.portfolio);

  @override
  List<Object> get props => [portfolio];
}
