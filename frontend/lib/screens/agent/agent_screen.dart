import 'dart:async';
import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:flutter_markdown/flutter_markdown.dart';
import '../../bloc/agent/agent_bloc.dart';
import '../../bloc/agent/agent_event.dart';
import '../../bloc/agent/agent_state.dart';

class AgentScreen extends StatefulWidget {
  const AgentScreen({super.key});

  @override
  State<AgentScreen> createState() => _AgentScreenState();
}

class _AgentScreenState extends State<AgentScreen>
    with TickerProviderStateMixin {
  late AnimationController _pulseController;
  Timer? _timeUpdateTimer;

  @override
  void initState() {
    super.initState();
    _pulseController = AnimationController(
      duration: const Duration(seconds: 2),
      vsync: this,
    );
    _pulseController.repeat(reverse: true);

    // 경과 시간을 1초마다 업데이트
    _timeUpdateTimer = Timer.periodic(const Duration(seconds: 1), (timer) {
      if (mounted) {
        setState(() {
          // UI 리빌드를 위한 상태 업데이트
        });
      }
    });
  }

  @override
  void dispose() {
    _pulseController.dispose();
    _timeUpdateTimer?.cancel();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return BlocBuilder<AgentBloc, AgentState>(
      builder: (context, state) {
        return Padding(
          padding: const EdgeInsets.all(16),
          child: Column(
            children: [
              // Status card
              _buildStatusCard(state),
              const SizedBox(height: 24),

              // Control buttons
              _buildControlButtons(state),
              const SizedBox(height: 24),

              // Progress section
              if (state is AgentRunning) ...[
                _buildProgressSection(state),
                const SizedBox(height: 24),
              ],

              // Results section: report_md Markdown 렌더링
              if (state is AgentCompleted) _buildResultsSection(state),

              // Error section
              if (state is AgentError) _buildErrorSection(state),
              if (state is AgentCancelled) _buildCancelledSection(state),
            ],
          ),
        );
      },
    );
  }

  Widget _buildStatusCard(AgentState state) {
    Color statusColor = Colors.grey;
    IconData statusIcon = Icons.help;
    String statusText = '알 수 없음';

    if (state is AgentIdle) {
      statusColor = Colors.grey;
      statusIcon = Icons.play_circle_outline;
      statusText = '대기 중';
    } else if (state is AgentRunning) {
      statusColor = Colors.blue;
      statusIcon = Icons.smart_toy;
      statusText = '실행 중';
    } else if (state is AgentCompleted) {
      statusColor = Colors.green;
      statusIcon = Icons.check_circle;
      statusText = '완료됨';
    } else if (state is AgentCancelled) {
      statusColor = Colors.orange;
      statusIcon = Icons.cancel;
      statusText = '취소됨';
    } else if (state is AgentError) {
      statusColor = Colors.red;
      statusIcon = Icons.error;
      statusText = '오류 발생';
    }

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(24),
        child: Row(
          children: [
            AnimatedBuilder(
              animation: _pulseController,
              builder: (context, child) {
                return Icon(
                  statusIcon,
                  size: 48,
                  color: statusColor.withOpacity(
                    state is AgentRunning
                        ? 0.5 + 0.5 * _pulseController.value
                        : 1.0,
                  ),
                );
              },
            ),
            const SizedBox(width: 16),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    '에이전트 상태',
                    style: Theme.of(context).textTheme.titleMedium,
                  ),
                  Text(
                    statusText,
                    style: Theme.of(context).textTheme.headlineSmall?.copyWith(
                      color: statusColor,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                  // Worker 상태들
                  if (state is AgentRunning && state.currentTask != null)
                    Text(
                      state.currentTask!,
                      style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                        color: Theme.of(
                          context,
                        ).colorScheme.onSurface.withOpacity(0.7),
                      ),
                    ),
                  if (state is AgentRunning && state.elapsedTime != null)
                    Text(
                      '경과 시간 (예상시간 10분): ${_formatDuration(state.elapsedTime!)}',
                      style: Theme.of(context).textTheme.bodySmall,
                    ),
                  if (state is AgentCompleted && state.elapsedTime != null)
                    Text(
                      '총 소요 시간: ${_formatDuration(state.elapsedTime!)}',
                      style: Theme.of(context).textTheme.bodySmall,
                    ),
                  if (state is AgentCancelled && state.elapsedTime != null)
                    Text(
                      '실행 시간: ${_formatDuration(state.elapsedTime!)}',
                      style: Theme.of(context).textTheme.bodySmall,
                    ),
                  if (state is AgentError && state.elapsedTime != null)
                    Text(
                      '실행 시간: ${_formatDuration(state.elapsedTime!)}',
                      style: Theme.of(context).textTheme.bodySmall,
                    ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildControlButtons(AgentState state) {
    final bool isRunning = state is AgentRunning || state is AgentLoading;
    final bool canCancel = state is AgentRunning;
    final bool isIdle = state is AgentIdle;

    return Column(
      children: [
        // 메인 실행 버튼들
        Row(
          children: [
            Expanded(
              child: ElevatedButton.icon(
                onPressed: isRunning
                    ? null
                    : () => context.read<AgentBloc>().add(AgentRunRequested()),
                icon: const Icon(Icons.play_arrow),
                label: const Text('에이전트 실행'),
                style: ElevatedButton.styleFrom(
                  minimumSize: const Size(double.infinity, 56),
                  padding: const EdgeInsets.symmetric(vertical: 16),
                ),
              ),
            ),
          ],
        ),

        const SizedBox(height: 12),

        // 제어 버튼들
        Row(
          children: [
            // 취소 버튼 (Worker 실행 중일 때만)
            if (canCancel) ...[
              Expanded(
                child: OutlinedButton.icon(
                  onPressed: canCancel
                      ? () {
                          context.read<AgentBloc>().add(
                            AgentTaskCancelRequested(state.taskId),
                          );
                        }
                      : null,
                  icon: const Icon(Icons.stop),
                  label: const Text('취소'),
                  style: OutlinedButton.styleFrom(
                    padding: const EdgeInsets.symmetric(vertical: 12),
                    foregroundColor: Colors.red,
                    side: const BorderSide(color: Colors.red),
                  ),
                ),
              ),
              const SizedBox(width: 16),
            ],

            // 초기화 버튼
            Expanded(
              child: OutlinedButton.icon(
                onPressed: isIdle
                    ? null
                    : () => context.read<AgentBloc>().add(AgentReset()),
                icon: const Icon(Icons.refresh),
                label: const Text('초기화'),
                style: OutlinedButton.styleFrom(
                  padding: const EdgeInsets.symmetric(vertical: 12),
                ),
              ),
            ),
          ],
        ),
      ],
    );
  }

  Widget _buildProgressSection(AgentRunning state) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(24),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('진행 상황', style: Theme.of(context).textTheme.titleLarge),
            const SizedBox(height: 16),
            LinearProgressIndicator(
              value: state.progress / 100,
              backgroundColor: Colors.grey[300],
            ),
            const SizedBox(height: 8),
            Text(
              '${state.progress.toStringAsFixed(1)}% 완료',
              style: Theme.of(context).textTheme.bodyLarge,
            ),
            if (state.currentTask != null) ...[
              const SizedBox(height: 8),
              Text(
                state.currentTask!,
                style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                  color: Theme.of(
                    context,
                  ).colorScheme.onSurface.withOpacity(0.7),
                ),
              ),
            ],
          ],
        ),
      ),
    );
  }

  Widget _buildResultsSection(AgentCompleted state) {
    final reportMd = state.reportMd;

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(24),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('실행 결과', style: Theme.of(context).textTheme.titleLarge),
            const SizedBox(height: 16),
            if (reportMd != null) ...[
              SizedBox(
                height: 500,
                child: Markdown(data: reportMd, selectable: true),
              ),
            ] else ...[
              Container(
                padding: const EdgeInsets.all(16),
                decoration: BoxDecoration(
                  color: Theme.of(context).colorScheme.surfaceVariant,
                  borderRadius: BorderRadius.circular(8),
                ),
                child: const Text(
                  '보고서 데이터를 찾을 수 없습니다.',
                  style: TextStyle(fontStyle: FontStyle.italic),
                ),
              ),
            ],
          ],
        ),
      ),
    );
  }

  Widget _buildErrorSection(AgentError state) {
    return Card(
      color: Theme.of(context).colorScheme.errorContainer,
      child: Padding(
        padding: const EdgeInsets.all(24),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Icon(
                  Icons.error,
                  color: Theme.of(context).colorScheme.onErrorContainer,
                ),
                const SizedBox(width: 8),
                Text(
                  '오류 발생',
                  style: Theme.of(context).textTheme.titleMedium?.copyWith(
                    color: Theme.of(context).colorScheme.onErrorContainer,
                  ),
                ),
              ],
            ),
            const SizedBox(height: 8),
            Text(
              state.message,
              style: TextStyle(
                color: Theme.of(context).colorScheme.onErrorContainer,
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildCancelledSection(AgentCancelled state) {
    return Card(
      color: Colors.orange.shade100,
      child: Padding(
        padding: const EdgeInsets.all(24),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Icon(Icons.cancel, color: Colors.orange.shade800),
                const SizedBox(width: 8),
                Text(
                  '태스크 취소됨',
                  style: Theme.of(context).textTheme.titleMedium?.copyWith(
                    color: Colors.orange.shade800,
                  ),
                ),
              ],
            ),
            const SizedBox(height: 8),
            Text(
              '에이전트 실행이 사용자에 의해 취소되었습니다.',
              style: TextStyle(color: Colors.orange.shade800),
            ),
            if (state.elapsedTime != null) ...[
              const SizedBox(height: 4),
              Text(
                '취소 전 실행 시간: ${_formatDuration(state.elapsedTime!)}',
                style: TextStyle(color: Colors.orange.shade600, fontSize: 12),
              ),
            ],
          ],
        ),
      ),
    );
  }

  String _formatDuration(Duration duration) {
    String twoDigits(int n) => n.toString().padLeft(2, '0');
    String minutes = twoDigits(duration.inMinutes.remainder(60));
    String seconds = twoDigits(duration.inSeconds.remainder(60));
    return '$minutes:$seconds';
  }
}
