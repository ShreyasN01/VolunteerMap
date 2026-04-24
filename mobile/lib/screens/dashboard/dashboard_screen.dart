import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:fl_chart/fl_chart.dart';
import '../../providers/dashboard_provider.dart';
import '../../providers/survey_provider.dart';
import '../../widgets/stat_card.dart';
import '../../widgets/survey_card.dart';
import '../../models/survey.dart';

class DashboardScreen extends StatefulWidget {
  const DashboardScreen({super.key});

  @override
  State<DashboardScreen> createState() => _DashboardScreenState();
}

class _DashboardScreenState extends State<DashboardScreen> {
  @override
  void initState() {
    super.initState();
    if (!mounted) return;
    context.read<DashboardProvider>().fetchStats();
    context.read<SurveyProvider>().fetchUrgentNeeds();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('VolunteerMap', style: TextStyle(fontWeight: FontWeight.bold, fontFamily: 'Poppins')),
        actions: [
          Consumer<DashboardProvider>(
            builder: (context, provider, child) {
              return Container(
                margin: const EdgeInsets.symmetric(vertical: 12, horizontal: 8),
                padding: const EdgeInsets.symmetric(horizontal: 12),
                decoration: BoxDecoration(
                  color: provider.totalSurveys > 0 ? Colors.green.withOpacity(0.1) : Colors.red.withOpacity(0.1),
                  borderRadius: BorderRadius.circular(20),
                  border: Border.all(color: provider.totalSurveys > 0 ? Colors.green : Colors.red, width: 1),
                ),
                child: Row(
                  children: [
                    Icon(Icons.circle, size: 8, color: provider.totalSurveys > 0 ? Colors.green : Colors.red),
                    const SizedBox(width: 6),
                    Text(
                      provider.totalSurveys > 0 ? 'LIVE' : 'OFFLINE',
                      style: TextStyle(fontSize: 10, fontWeight: FontWeight.bold, color: provider.totalSurveys > 0 ? Colors.green : Colors.red),
                    ),
                  ],
                ),
              );
            },
          ),
          IconButton(icon: const Icon(Icons.notifications_none), onPressed: () {}),
        ],
      ),
      body: RefreshIndicator(
        onRefresh: () async {
          await context.read<DashboardProvider>().fetchStats();
          await context.read<SurveyProvider>().fetchUrgentNeeds();
        },
        child: SingleChildScrollView(
          physics: const AlwaysScrollableScrollPhysics(),
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // Stats Row
              Consumer<DashboardProvider>(
                builder: (context, provider, child) {
                  return Row(
                    children: [
                      StatCard(title: 'Total Surveys', value: provider.totalSurveys.toString(), color: Colors.blue, icon: Icons.assignment),
                      const SizedBox(width: 12),
                      StatCard(title: 'Active Volunteers', value: provider.activeVolunteers.toString(), color: Colors.green, icon: Icons.people),
                      const SizedBox(width: 12),
                      StatCard(title: 'Urgent Needs', value: provider.urgentCount.toString(), color: Colors.red, icon: Icons.warning),
                    ],
                  );
                },
              ),
              const SizedBox(height: 24),
              
              // Category Chart
              const Text('Needs by Category', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold, fontFamily: 'Poppins')),
              const SizedBox(height: 16),
              SizedBox(
                height: 200,
                child: Consumer<DashboardProvider>(
                  builder: (context, provider, child) {
                    final data = provider.categoryBreakdown;
                    if (data.isEmpty) return const Center(child: Text('No data available'));
                    
                    return BarChart(
                      BarChartData(
                        alignment: BarChartAlignment.spaceAround,
                        maxY: data.values.fold(0, (prev, element) => element > prev ? element : prev).toDouble() + 2,
                        barGroups: [
                          _buildBarGroup(0, data['healthcare']?.toDouble() ?? 0, Colors.red),
                          _buildBarGroup(1, data['food']?.toDouble() ?? 0, Colors.orange),
                          _buildBarGroup(2, data['education']?.toDouble() ?? 0, Colors.blue),
                          _buildBarGroup(3, data['sanitation']?.toDouble() ?? 0, Colors.green),
                          _buildBarGroup(4, data['employment']?.toDouble() ?? 0, Colors.purple),
                        ],
                        titlesData: FlTitlesData(
                          show: true,
                          bottomTitles: AxisTitles(
                            sideTitles: SideTitles(
                              showTitles: true,
                              getTitlesWidget: (value, meta) {
                                switch (value.toInt()) {
                                  case 0: return const Text('Health', style: TextStyle(fontSize: 10));
                                  case 1: return const Text('Food', style: TextStyle(fontSize: 10));
                                  case 2: return const Text('Edu', style: TextStyle(fontSize: 10));
                                  case 3: return const Text('San', style: TextStyle(fontSize: 10));
                                  case 4: return const Text('Emp', style: TextStyle(fontSize: 10));
                                  default: return const Text('');
                                }
                              },
                            ),
                          ),
                          leftTitles: const AxisTitles(sideTitles: SideTitles(showTitles: false)),
                          topTitles: const AxisTitles(sideTitles: SideTitles(showTitles: false)),
                          rightTitles: const AxisTitles(sideTitles: SideTitles(showTitles: false)),
                        ),
                        borderData: FlBorderData(show: false),
                        gridData: const FlGridData(show: false),
                      ),
                    );
                  },
                ),
              ),
              const SizedBox(height: 24),
              
              // Urgent Needs Section
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  const Text('🚨 Urgent Needs', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold, fontFamily: 'Poppins')),
                  TextButton(onPressed: () {}, child: const Text('View all')),
                ],
              ),
              const SizedBox(height: 8),
              Consumer<SurveyProvider>(
                builder: (context, provider, child) {
                  if (provider.isLoading && provider.urgentNeeds.isEmpty) {
                    return const Center(child: CircularProgressIndicator());
                  }
                  return ListView.builder(
                    shrinkWrap: true,
                    physics: const NeverScrollableScrollPhysics(),
                    itemCount: provider.urgentNeeds.length,
                    itemBuilder: (context, index) {
                      return SurveyCard(survey: provider.urgentNeeds[index]);
                    },
                  );
                },
              ),
              const SizedBox(height: 24),
              
              // Quick Actions
              Row(
                children: [
                  Expanded(
                    child: ElevatedButton.icon(
                      onPressed: () {},
                      icon: const Icon(Icons.add),
                      label: const Text('Submit Survey'),
                      style: ElevatedButton.styleFrom(backgroundColor: Colors.teal, foregroundColor: Colors.white),
                    ),
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: ElevatedButton.icon(
                      onPressed: () {},
                      icon: const Icon(Icons.bolt),
                      label: const Text('Run AI Match'),
                      style: ElevatedButton.styleFrom(backgroundColor: Colors.purple, foregroundColor: Colors.white),
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 40),
            ],
          ),
        ),
      ),
    );
  }

  BarChartGroupData _buildBarGroup(int x, double y, Color color) {
    return BarChartGroupData(
      x: x,
      barRods: [
        BarChartRodData(toY: y, color: color, width: 20, borderRadius: BorderRadius.circular(4)),
      ],
    );
  }
}
