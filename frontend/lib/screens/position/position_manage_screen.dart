import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:go_router/go_router.dart';
import '../../bloc/position/position_bloc.dart';
import '../../bloc/position/position_event.dart';
import '../../bloc/position/position_state.dart';
import '../../bloc/portfolio/portfolio_bloc.dart';
import '../../bloc/portfolio/portfolio_event.dart';
import '../../bloc/portfolio/portfolio_state.dart';
import '../../widgets/common/custom_button.dart';
import '../../widgets/common/custom_snackbar.dart';
import '../../widgets/common/stock_search_field.dart';

class PositionManageScreen extends StatefulWidget {
  final int? positionId; // null이면 생성 모드, 값이 있으면 수정 모드

  const PositionManageScreen({super.key, this.positionId});

  @override
  State<PositionManageScreen> createState() => _PositionManageScreenState();
}

class _PositionManageScreenState extends State<PositionManageScreen> {
  final _formKey = GlobalKey<FormState>();
  final _tickerController = TextEditingController();
  final _sharesController = TextEditingController();
  final _priceController = TextEditingController();

  bool get isEditMode => widget.positionId != null;

  @override
  void initState() {
    super.initState();

    // 포트폴리오 정보가 없으면 로드
    final portfolioState = context.read<PortfolioBloc>().state;
    if (portfolioState is! PortfolioLoadedState) {
      context.read<PortfolioBloc>().add(PortfolioLoadRequested());
    }

    if (isEditMode) {
      // 수정 모드인 경우 기존 포지션 데이터 로드
      context.read<PositionBloc>().add(
        PositionLoadRequested(positionId: widget.positionId!),
      );
    }
  }

  @override
  void dispose() {
    _tickerController.dispose();
    _sharesController.dispose();
    _priceController.dispose();
    super.dispose();
  }

  void _submitForm() {
    if (!_formKey.currentState!.validate()) return;

    // 현재 포트폴리오 상태에서 포트폴리오 ID 가져오기
    final portfolioState = context.read<PortfolioBloc>().state;
    int? portfolioId;

    if (portfolioState is PortfolioLoadedState) {
      portfolioId =
          portfolioState.selectedPortfolio?.id ??
          (portfolioState.portfolios.isNotEmpty
              ? portfolioState.portfolios.first.id
              : null);
    }

    if (portfolioId == null) {
      // 포트폴리오 정보가 없으면 오류 표시
      ScaffoldMessenger.of(
        context,
      ).showSnackBar(const SnackBar(content: Text('포트폴리오 정보를 불러올 수 없습니다')));
      return;
    }

    final positionData = {
      'portfolio_id': portfolioId, // 동적으로 가져온 포트폴리오 ID 사용
      'ticker': _tickerController.text.trim().toUpperCase(),
      'total_shares': double.parse(_sharesController.text),
      'avg_buy_price': double.parse(_priceController.text),
    };

    debugPrint('포지션 생성/수정 데이터: $positionData'); // 디버깅용

    if (isEditMode) {
      context.read<PositionBloc>().add(
        PositionUpdateRequested(
          positionId: widget.positionId!,
          updates: positionData,
        ),
      );
    } else {
      context.read<PositionBloc>().add(
        PositionCreateRequested(positionData: positionData),
      );
    }
  }

  void _deletePosition() {
    if (!isEditMode) return;

    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('포지션 삭제'),
        content: const Text('정말로 이 포지션을 삭제하시겠습니까?'),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(context).pop(),
            child: const Text('취소'),
          ),
          TextButton(
            onPressed: () {
              Navigator.of(context).pop();
              context.read<PositionBloc>().add(
                PositionDeleteRequested(positionId: widget.positionId!),
              );
            },
            style: TextButton.styleFrom(foregroundColor: Colors.red),
            child: const Text('삭제'),
          ),
        ],
      ),
    );
  }

  // 현재 포트폴리오의 통화 심볼 가져오기
  String _getCurrencySymbol() {
    final portfolioState = context.read<PortfolioBloc>().state;
    if (portfolioState is PortfolioLoadedState &&
        portfolioState.portfolios.isNotEmpty) {
      final baseCurrency = portfolioState.portfolios.first.baseCurrency;
      // CurrencyFormatter에서 심볼 매핑 사용
      const currencySymbols = {
        'USD': '\$',
        'KRW': '₩',
        'EUR': '€',
        'JPY': '¥',
        'GBP': '£',
        'CNY': '¥',
        'CAD': 'C\$',
        'AUD': 'A\$',
        'CHF': 'CHF',
        'HKD': 'HK\$',
        'SGD': 'S\$',
      };
      return currencySymbols[baseCurrency.toUpperCase()] ?? baseCurrency;
    }
    return '\$'; // 기본값
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text(isEditMode ? '포지션 수정' : '포지션 추가'),
        backgroundColor: Colors.transparent,
        elevation: 0,
        actions: [
          if (isEditMode)
            IconButton(
              onPressed: _deletePosition,
              icon: const Icon(Icons.delete_outline),
              tooltip: '포지션 삭제',
              color: Colors.red,
            ),
        ],
      ),
      body: BlocConsumer<PositionBloc, PositionState>(
        listener: (context, state) {
          if (state is PositionLoaded && isEditMode) {
            // 수정 모드에서 데이터 로드 완료 시 폼 필드 채우기
            final position = state.position;
            _tickerController.text = position.ticker;
            _sharesController.text = position.totalShares.toString();
            _priceController.text = position.avgBuyPrice.toString();
          } else if (state is PositionSuccess) {
            // 성공 시 포트폴리오 새로고침하고 뒤로가기
            context.read<PortfolioBloc>().add(PortfolioLoadRequested());
            CustomSnackBar.showSuccess(context, message: state.message);
            context.pop();
          } else if (state is PositionError) {
            CustomSnackBar.showError(context, message: state.message);
          }
        },
        builder: (context, state) {
          return Padding(
            padding: const EdgeInsets.all(24),
            child: Column(
              children: [
                Expanded(
                  child: Form(
                    key: _formKey,
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        // 설명 텍스트
                        Card(
                          child: Padding(
                            padding: const EdgeInsets.all(16),
                            child: Row(
                              children: [
                                Icon(
                                  Icons.info_outline,
                                  color: Theme.of(context).colorScheme.primary,
                                ),
                                const SizedBox(width: 12),
                                Expanded(
                                  child: Text(
                                    isEditMode
                                        ? '포지션 정보를 수정하세요'
                                        : '새로운 포지션을 추가하세요',
                                    style: Theme.of(
                                      context,
                                    ).textTheme.bodyMedium,
                                  ),
                                ),
                              ],
                            ),
                          ),
                        ),
                        const SizedBox(height: 32),

                        // 종목 코드
                        Text(
                          '종목 코드',
                          style: Theme.of(context).textTheme.titleSmall
                              ?.copyWith(fontWeight: FontWeight.bold),
                        ),
                        const SizedBox(height: 8),
                        StockSearchField(
                          controller: _tickerController,
                          hintText: 'AAPL, MSFT 등',
                          decoration: const InputDecoration(
                            hintText: 'AAPL, MSFT 등 (입력 시 자동완성)',
                            border: OutlineInputBorder(),
                          ),
                          validator: (value) {
                            if (value == null || value.trim().isEmpty) {
                              return '종목 코드를 입력해주세요';
                            }
                            return null;
                          },
                        ),
                        const SizedBox(height: 24),

                        // 보유 수량
                        Text(
                          '보유 수량',
                          style: Theme.of(context).textTheme.titleSmall
                              ?.copyWith(fontWeight: FontWeight.bold),
                        ),
                        const SizedBox(height: 8),
                        TextFormField(
                          controller: _sharesController,
                          decoration: const InputDecoration(
                            hintText: '예: 100',
                            suffixText: '주',
                            border: OutlineInputBorder(),
                          ),
                          keyboardType: const TextInputType.numberWithOptions(
                            decimal: true,
                          ),
                          validator: (value) {
                            if (value == null || value.trim().isEmpty) {
                              return '보유 수량을 입력해주세요';
                            }
                            final shares = double.tryParse(value);
                            if (shares == null || shares <= 0) {
                              return '올바른 수량을 입력해주세요';
                            }
                            return null;
                          },
                        ),
                        const SizedBox(height: 24),

                        // 평균 매수가
                        Text(
                          '평균 매수가',
                          style: Theme.of(context).textTheme.titleSmall
                              ?.copyWith(fontWeight: FontWeight.bold),
                        ),
                        const SizedBox(height: 8),
                        TextFormField(
                          controller: _priceController,
                          decoration: InputDecoration(
                            hintText: '예: 150.25',
                            prefixText: '${_getCurrencySymbol()} ',
                            border: const OutlineInputBorder(),
                          ),
                          keyboardType: const TextInputType.numberWithOptions(
                            decimal: true,
                          ),
                          validator: (value) {
                            if (value == null || value.trim().isEmpty) {
                              return '평균 매수가를 입력해주세요';
                            }
                            final price = double.tryParse(value);
                            if (price == null || price <= 0) {
                              return '올바른 가격을 입력해주세요';
                            }
                            return null;
                          },
                        ),
                        const Spacer(),
                      ],
                    ),
                  ),
                ),

                // 버튼
                SizedBox(
                  width: double.infinity,
                  child: CustomButton(
                    onPressed: state is PositionLoading ? null : _submitForm,
                    isLoading: state is PositionLoading,
                    text: isEditMode ? '포지션 수정' : '포지션 추가',
                  ),
                ),
              ],
            ),
          );
        },
      ),
    );
  }
}
