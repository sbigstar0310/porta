import 'package:flutter_bloc/flutter_bloc.dart';
import '../../services/api_service.dart';
import 'portfolio_event.dart';
import 'portfolio_state.dart';

class PortfolioBloc extends Bloc<PortfolioEvent, PortfolioState> {
  final ApiService _apiService = ApiService();

  PortfolioBloc() : super(PortfolioInitial()) {
    on<PortfolioLoadRequested>(_onPortfolioLoaded);
    on<PortfolioCreated>(_onPortfolioCreated);
    on<PortfolioUpdated>(_onPortfolioUpdated);
    on<PortfolioSelected>(_onPortfolioSelected);
  }

  Future<void> _onPortfolioLoaded(
    PortfolioLoadRequested event,
    Emitter<PortfolioState> emit,
  ) async {
    emit(PortfolioLoading());

    try {
      final portfolio = await _apiService.getPortfolio();
      emit(
        PortfolioLoadedState(
          portfolios: [portfolio],
          selectedPortfolio: portfolio,
        ),
      );
    } catch (e) {
      emit(const PortfolioError('포트폴리오를 불러올 수 없습니다. 다시 시도해주세요.'));
    }
  }

  Future<void> _onPortfolioCreated(
    PortfolioCreated event,
    Emitter<PortfolioState> emit,
  ) async {
    emit(PortfolioLoading());

    try {
      final newPortfolio = await _apiService.createPortfolio(event.name);

      final currentState = state;
      if (currentState is PortfolioLoadedState) {
        final updatedPortfolios = [...currentState.portfolios, newPortfolio];
        emit(
          PortfolioLoadedState(
            portfolios: updatedPortfolios,
            selectedPortfolio: newPortfolio,
          ),
        );
      } else {
        emit(
          PortfolioLoadedState(
            portfolios: [newPortfolio],
            selectedPortfolio: newPortfolio,
          ),
        );
      }
    } catch (e) {
      emit(PortfolioError('포트폴리오 생성 실패: $e'));
    }
  }

  Future<void> _onPortfolioUpdated(
    PortfolioUpdated event,
    Emitter<PortfolioState> emit,
  ) async {
    emit(PortfolioLoading());

    try {
      final updatedPortfolio = await _apiService.updatePortfolio(
        event.portfolioId,
        event.updates,
      );

      emit(
        PortfolioLoadedState(
          portfolios: [updatedPortfolio],
          selectedPortfolio: updatedPortfolio,
        ),
      );
    } catch (e) {
      emit(PortfolioError('포트폴리오 업데이트 실패: $e'));
    }
  }

  void _onPortfolioSelected(
    PortfolioSelected event,
    Emitter<PortfolioState> emit,
  ) {
    final currentState = state;
    if (currentState is PortfolioLoadedState) {
      emit(currentState.copyWith(selectedPortfolio: event.portfolio));
    }
  }
}
