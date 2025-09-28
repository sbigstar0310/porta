import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:go_router/go_router.dart';
import 'package:intl/intl.dart';
import '../../bloc/portfolio/portfolio_bloc.dart';
import '../../bloc/portfolio/portfolio_event.dart';
import '../../bloc/portfolio/portfolio_state.dart';
import '../../models/portfolio.dart';
import '../../utils/currency_formatter.dart';

class PositionListScreen extends StatefulWidget {
  const PositionListScreen({super.key});

  @override
  State<PositionListScreen> createState() => _PositionListScreenState();
}

class _PositionListScreenState extends State<PositionListScreen> {
  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      context.read<PortfolioBloc>().add(PortfolioLoadRequested());
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      floatingActionButton: FloatingActionButton(
        onPressed: () => context.go('/position/add'),
        tooltip: '포지션 추가',
        child: const Icon(Icons.add),
      ),
      body: Column(
        children: [
          // Header
          Container(
            width: double.infinity,
            padding: const EdgeInsets.all(24),
            decoration: BoxDecoration(
              gradient: LinearGradient(
                colors: [
                  Theme.of(context).colorScheme.primary,
                  Theme.of(context).colorScheme.primary.withOpacity(0.8),
                ],
                begin: Alignment.topLeft,
                end: Alignment.bottomRight,
              ),
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    Icon(
                      Icons.business_outlined,
                      color: Theme.of(context).colorScheme.onPrimary,
                      size: 32,
                    ),
                    const SizedBox(width: 16),
                    Text(
                      '포지션 관리',
                      style: Theme.of(context).textTheme.headlineSmall
                          ?.copyWith(
                            color: Theme.of(context).colorScheme.onPrimary,
                            fontWeight: FontWeight.bold,
                          ),
                    ),
                  ],
                ),
                const SizedBox(height: 8),
                Text(
                  '보유 종목을 관리하고 수정할 수 있습니다',
                  style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                    color: Theme.of(
                      context,
                    ).colorScheme.onPrimary.withOpacity(0.9),
                  ),
                ),
              ],
            ),
          ),

          // Positions List
          Expanded(
            child: BlocBuilder<PortfolioBloc, PortfolioState>(
              builder: (context, state) {
                if (state is PortfolioLoading) {
                  return const Center(child: CircularProgressIndicator());
                }

                if (state is PortfolioError) {
                  return Center(
                    child: Column(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        Icon(
                          Icons.error_outline,
                          size: 64,
                          color: Colors.red.withOpacity(0.6),
                        ),
                        const SizedBox(height: 16),
                        Text(
                          '포지션을 불러올 수 없습니다',
                          style: Theme.of(context).textTheme.titleLarge
                              ?.copyWith(
                                color: Colors.red,
                                fontWeight: FontWeight.bold,
                              ),
                        ),
                        const SizedBox(height: 8),
                        Padding(
                          padding: const EdgeInsets.symmetric(horizontal: 32),
                          child: Text(
                            state.message,
                            textAlign: TextAlign.center,
                            style: Theme.of(context).textTheme.bodyMedium
                                ?.copyWith(
                                  color: Theme.of(
                                    context,
                                  ).colorScheme.onSurface.withOpacity(0.6),
                                ),
                          ),
                        ),
                        const SizedBox(height: 24),
                        ElevatedButton.icon(
                          onPressed: () => context.read<PortfolioBloc>().add(
                            PortfolioLoadRequested(),
                          ),
                          icon: const Icon(Icons.refresh),
                          label: const Text('다시 시도'),
                        ),
                      ],
                    ),
                  );
                }

                if (state is PortfolioLoadedState) {
                  final portfolio = state.portfolios.isNotEmpty
                      ? state.portfolios.first
                      : null;

                  if (portfolio == null || portfolio.positions.isEmpty) {
                    return Center(
                      child: Column(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          Icon(
                            Icons.business_outlined,
                            size: 64,
                            color: Theme.of(
                              context,
                            ).colorScheme.onSurface.withOpacity(0.4),
                          ),
                          const SizedBox(height: 16),
                          Text(
                            '보유 포지션이 없습니다',
                            style: Theme.of(context).textTheme.titleMedium
                                ?.copyWith(
                                  color: Theme.of(
                                    context,
                                  ).colorScheme.onSurface.withOpacity(0.6),
                                ),
                          ),
                          const SizedBox(height: 8),
                          Text(
                            '첫 번째 포지션을 추가해보세요',
                            style: Theme.of(context).textTheme.bodyMedium
                                ?.copyWith(
                                  color: Theme.of(
                                    context,
                                  ).colorScheme.onSurface.withOpacity(0.4),
                                ),
                          ),
                          const SizedBox(height: 24),
                          ElevatedButton.icon(
                            onPressed: () => context.go('/position/add'),
                            icon: const Icon(Icons.add),
                            label: const Text('포지션 추가'),
                          ),
                        ],
                      ),
                    );
                  }

                  return RefreshIndicator(
                    onRefresh: () async {
                      context.read<PortfolioBloc>().add(
                        PortfolioLoadRequested(),
                      );
                    },
                    child: ListView.builder(
                      padding: const EdgeInsets.all(24),
                      itemCount: portfolio.positions.length,
                      itemBuilder: (context, index) {
                        final position = portfolio.positions[index];
                        return _buildPositionCard(position, portfolio);
                      },
                    ),
                  );
                }

                return const SizedBox.shrink();
              },
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildPositionCard(Position position, Portfolio portfolio) {
    final currencyFormat = CurrencyFormatter.createFormatter(
      portfolio.baseCurrency,
    );
    final percentFormat = NumberFormat('#,##0.00');
    final sharesFormat = NumberFormat('#,##0.###');

    return Container(
      margin: const EdgeInsets.only(bottom: 16),
      child: Card(
        elevation: 2,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
        child: InkWell(
          onTap: () => context.go('/position/edit/${position.id}'),
          borderRadius: BorderRadius.circular(16),
          child: Padding(
            padding: const EdgeInsets.all(20),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                // Header
                Row(
                  children: [
                    Container(
                      padding: const EdgeInsets.all(12),
                      decoration: BoxDecoration(
                        color: Theme.of(context).colorScheme.primaryContainer,
                        borderRadius: BorderRadius.circular(12),
                      ),
                      child: Icon(
                        Icons.trending_up,
                        color: Theme.of(context).colorScheme.onPrimaryContainer,
                      ),
                    ),
                    const SizedBox(width: 16),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            position.ticker,
                            style: Theme.of(context).textTheme.titleLarge
                                ?.copyWith(fontWeight: FontWeight.bold),
                          ),
                          Text(
                            '${sharesFormat.format(position.totalShares)}주',
                            style: Theme.of(context).textTheme.bodyMedium
                                ?.copyWith(
                                  color: Theme.of(
                                    context,
                                  ).colorScheme.onSurface.withOpacity(0.6),
                                ),
                          ),
                        ],
                      ),
                    ),
                    Column(
                      crossAxisAlignment: CrossAxisAlignment.end,
                      children: [
                        Text(
                          currencyFormat.format(
                            position.currentMarketValue ?? 0,
                          ),
                          style: Theme.of(context).textTheme.titleLarge
                              ?.copyWith(fontWeight: FontWeight.bold),
                        ),
                        Text(
                          '${(position.unrealizedPnlPct ?? 0) >= 0 ? '+' : ''}${percentFormat.format(position.unrealizedPnlPct ?? 0)}%',
                          style: Theme.of(context).textTheme.bodyMedium
                              ?.copyWith(
                                color: (position.unrealizedPnlPct ?? 0) >= 0
                                    ? Colors.green
                                    : Colors.red,
                                fontWeight: FontWeight.bold,
                              ),
                        ),
                      ],
                    ),
                    const SizedBox(width: 8),
                    Icon(
                      Icons.chevron_right,
                      color: Theme.of(
                        context,
                      ).colorScheme.onSurface.withOpacity(0.4),
                    ),
                  ],
                ),
                const SizedBox(height: 16),

                // Quick stats
                Row(
                  children: [
                    Expanded(
                      child: _buildQuickStat(
                        '평균 단가',
                        currencyFormat.format(position.avgBuyPrice),
                        Icons.payment_outlined,
                      ),
                    ),
                    const SizedBox(width: 16),
                    Expanded(
                      child: _buildQuickStat(
                        '현재 가격',
                        currencyFormat.format(
                          position.currentPrice ?? position.avgBuyPrice,
                        ),
                        Icons.price_change_outlined,
                      ),
                    ),
                    const SizedBox(width: 16),
                    Expanded(
                      child: _buildQuickStat(
                        '평가 손익',
                        currencyFormat.format(position.unrealizedPnl ?? 0),
                        Icons.account_balance_outlined,
                        isProfit: (position.unrealizedPnl ?? 0) >= 0,
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
  }

  Widget _buildQuickStat(
    String title,
    String value,
    IconData icon, {
    bool? isProfit,
  }) {
    Color? textColor;
    if (isProfit != null) {
      textColor = isProfit ? Colors.green : Colors.red;
    }

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          children: [
            Icon(
              icon,
              size: 14,
              color: Theme.of(context).colorScheme.onSurface.withOpacity(0.6),
            ),
            const SizedBox(width: 4),
            Flexible(
              child: Text(
                title,
                style: Theme.of(context).textTheme.bodySmall?.copyWith(
                  color: Theme.of(
                    context,
                  ).colorScheme.onSurface.withOpacity(0.6),
                ),
                overflow: TextOverflow.ellipsis,
              ),
            ),
          ],
        ),
        const SizedBox(height: 4),
        Text(
          value,
          style: Theme.of(context).textTheme.bodyMedium?.copyWith(
            fontWeight: FontWeight.bold,
            color: textColor,
          ),
          overflow: TextOverflow.ellipsis,
        ),
      ],
    );
  }
}
