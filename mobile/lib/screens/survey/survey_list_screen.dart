import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../providers/survey_provider.dart';
import '../../widgets/survey_card.dart';

class SurveyListScreen extends StatefulWidget {
  const SurveyListScreen({super.key});

  @override
  State<SurveyListScreen> createState() => _SurveyListScreenState();
}

class _SurveyListScreenState extends State<SurveyListScreen> {
  String _searchQuery = '';
  String _selectedCategory = 'All';
  final List<String> _categories = ['All', 'Healthcare', 'Food', 'Education', 'Sanitation', 'Employment'];

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      context.read<SurveyProvider>().fetchSurveys();
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Community Surveys')),
      body: Column(
        children: [
          Padding(
            padding: const EdgeInsets.all(16.0),
            child: SearchBar(
              hintText: 'Search by description or district...',
              onChanged: (value) => setState(() => _searchQuery = value),
              leading: const Icon(Icons.search),
            ),
          ),
          SingleChildScrollView(
            scrollDirection: Axis.horizontal,
            padding: const EdgeInsets.symmetric(horizontal: 16),
            child: Row(
              children: _categories.map((cat) {
                return Padding(
                  padding: const EdgeInsets.only(right: 8),
                  child: FilterChip(
                    label: Text(cat),
                    selected: _selectedCategory == cat,
                    onSelected: (val) => setState(() => _selectedCategory = cat),
                  ),
                );
              }).toList(),
            ),
          ),
          const SizedBox(height: 12),
          Expanded(
            child: Consumer<SurveyProvider>(
              builder: (context, provider, child) {
                final surveys = provider.filterByCategory(_selectedCategory).where((s) {
                  return s.description.toLowerCase().contains(_searchQuery.toLowerCase()) ||
                         s.district.toLowerCase().contains(_searchQuery.toLowerCase());
                }).toList();

                if (provider.isLoading && surveys.isEmpty) {
                  return const Center(child: CircularProgressIndicator());
                }

                if (surveys.isEmpty) {
                  return Center(
                    child: Column(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        Icon(Icons.inbox, size: 64, color: Colors.grey[400]),
                        const SizedBox(height: 16),
                        Text('No surveys found', style: TextStyle(color: Colors.grey[600])),
                      ],
                    ),
                  );
                }

                return RefreshIndicator(
                  onRefresh: provider.fetchSurveys,
                  child: ListView.builder(
                    padding: const EdgeInsets.symmetric(horizontal: 16),
                    itemCount: surveys.length,
                    itemBuilder: (context, index) {
                      return SurveyCard(survey: surveys[index]);
                    },
                  ),
                );
              },
            ),
          ),
        ],
      ),
    );
  }
}
