import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:go_router/go_router.dart';
import '../../bloc/portfolio/portfolio_bloc.dart';
import '../../bloc/portfolio/portfolio_event.dart';
import '../../bloc/portfolio/portfolio_state.dart';
import '../../models/portfolio.dart';
import '../../widgets/common/custom_snackbar.dart';

class PortfolioEditScreen extends StatefulWidget {
  const PortfolioEditScreen({super.key});

  @override
  State<PortfolioEditScreen> createState() => _PortfolioEditScreenState();
}

class _PortfolioEditScreenState extends State<PortfolioEditScreen> {
  final _formKey = GlobalKey<FormState>();
  final _cashController = TextEditingController();
  final _baseCurrencyController = TextEditingController();

  bool _isEditing = false;
  Portfolio? _editingPortfolio;

  // 지원되는 통화 목록
  final List<String> _supportedCurrencies = [
    'USD',
    'KRW',
    'EUR',
    'JPY',
    'GBP',
    'CAD',
    'AUD',
  ];

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      final portfolioState = context.read<PortfolioBloc>().state;
      if (portfolioState is PortfolioLoadedState) {
        _editingPortfolio = portfolioState.selectedPortfolio;

        if (_editingPortfolio != null) {
          _isEditing = true;
          _cashController.text = _editingPortfolio!.cash.toString();
          _baseCurrencyController.text = _editingPortfolio!.baseCurrency;
        }
      }

      setState(() {});
    });
  }

  @override
  void dispose() {
    _cashController.dispose();
    _baseCurrencyController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text(_isEditing ? '포트폴리오 수정' : '포트폴리오 생성'),
        backgroundColor: Theme.of(context).colorScheme.surface,
        elevation: 0,
        scrolledUnderElevation: 1,
        centerTitle: true,
      ),
      body: BlocListener<PortfolioBloc, PortfolioState>(
        listener: (context, state) {
          if (state is PortfolioLoadedState) {
            CustomSnackBar.showSuccess(context, message: '포트폴리오가 저장되었습니다.');
            context.go('/portfolio');
          } else if (state is PortfolioError) {
            CustomSnackBar.showError(context, message: state.message);
          }
        },
        child: BlocBuilder<PortfolioBloc, PortfolioState>(
          builder: (context, state) {
            return Center(
              child: ConstrainedBox(
                constraints: const BoxConstraints(maxWidth: 600),
                child: Padding(
                  padding: const EdgeInsets.all(24),
                  child: Form(
                    key: _formKey,
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.stretch,
                      children: [
                        Card(
                          child: Padding(
                            padding: const EdgeInsets.all(16),
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Text(
                                  '기본 정보',
                                  style: Theme.of(context).textTheme.titleLarge,
                                ),
                                const SizedBox(height: 16),
                                TextFormField(
                                  controller: _cashController,
                                  decoration: const InputDecoration(
                                    labelText: '현금 (Cash)',
                                    border: OutlineInputBorder(),
                                    suffixText: '기본 통화 단위',
                                  ),
                                  keyboardType:
                                      const TextInputType.numberWithOptions(
                                        decimal: true,
                                      ),
                                  validator: (value) {
                                    if (value == null || value.trim().isEmpty) {
                                      return '현금 금액을 입력해주세요';
                                    }
                                    if (double.tryParse(value) == null) {
                                      return '올바른 숫자를 입력해주세요';
                                    }
                                    if (double.parse(value) < 0) {
                                      return '현금 금액은 0 이상이어야 합니다';
                                    }
                                    return null;
                                  },
                                ),
                                const SizedBox(height: 16),
                                DropdownButtonFormField<String>(
                                  value: _baseCurrencyController.text.isNotEmpty
                                      ? _baseCurrencyController.text
                                      : null,
                                  decoration: const InputDecoration(
                                    labelText: '기본 통화',
                                    border: OutlineInputBorder(),
                                  ),
                                  items: _supportedCurrencies.map((
                                    String currency,
                                  ) {
                                    return DropdownMenuItem<String>(
                                      value: currency,
                                      child: Text(currency),
                                    );
                                  }).toList(),
                                  onChanged: (String? newValue) {
                                    if (newValue != null) {
                                      _baseCurrencyController.text = newValue;
                                    }
                                  },
                                  validator: (value) {
                                    if (value == null || value.isEmpty) {
                                      return '기본 통화를 선택해주세요';
                                    }
                                    return null;
                                  },
                                ),
                              ],
                            ),
                          ),
                        ),
                        const SizedBox(height: 16),
                        Card(
                          child: Padding(
                            padding: const EdgeInsets.all(16),
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Text(
                                  '안내',
                                  style: Theme.of(
                                    context,
                                  ).textTheme.titleMedium,
                                ),
                                const SizedBox(height: 8),
                                Text(
                                  '포트폴리오의 현금 보유량과 기본 통화를 설정할 수 있습니다.\n'
                                  '종목 추가 및 거래 내역 관리는 포지션 관리 메뉴에서 이용하실 수 있습니다.',
                                  style: Theme.of(context).textTheme.bodyMedium
                                      ?.copyWith(
                                        color: Theme.of(context)
                                            .colorScheme
                                            .onSurface
                                            .withOpacity(0.7),
                                      ),
                                ),
                              ],
                            ),
                          ),
                        ),
                        const Spacer(),
                        Row(
                          children: [
                            Expanded(
                              child: OutlinedButton(
                                onPressed: () => context.go('/portfolio'),
                                child: const Text('취소'),
                              ),
                            ),
                            const SizedBox(width: 16),
                            Expanded(
                              child: ElevatedButton(
                                onPressed: state is PortfolioLoading
                                    ? null
                                    : () => _savePortfolio(),
                                child: state is PortfolioLoading
                                    ? const SizedBox(
                                        height: 20,
                                        width: 20,
                                        child: CircularProgressIndicator(
                                          strokeWidth: 2,
                                        ),
                                      )
                                    : Text(_isEditing ? '수정' : '생성'),
                              ),
                            ),
                          ],
                        ),
                      ],
                    ),
                  ),
                ),
              ),
            );
          },
        ),
      ),
    );
  }

  void _savePortfolio() {
    if (!_formKey.currentState!.validate()) return;

    if (_isEditing && _editingPortfolio != null) {
      // 포트폴리오 업데이트
      final cash = double.parse(_cashController.text);
      final baseCurrency = _baseCurrencyController.text;

      final updates = <String, dynamic>{};

      // 변경된 값만 업데이트에 포함
      if (cash != _editingPortfolio!.cash) {
        updates['cash'] = cash;
      }

      if (baseCurrency != _editingPortfolio!.baseCurrency) {
        updates['base_currency'] = baseCurrency;
      }

      if (updates.isNotEmpty) {
        context.read<PortfolioBloc>().add(
          PortfolioUpdated(
            portfolioId: _editingPortfolio!.id,
            updates: updates,
          ),
        );
      } else {
        // 변경사항이 없으면 그냥 이전 화면으로
        CustomSnackBar.showInfo(context, message: '변경사항이 없습니다.');
        context.go('/portfolio');
      }
    } else {
      // 새 포트폴리오 생성은 백엔드에서 지원하지 않으므로 안내 메시지
      CustomSnackBar.showInfo(context, message: '포트폴리오는 계정 생성 시 자동으로 생성됩니다.');
      context.go('/portfolio');
    }
  }
}
