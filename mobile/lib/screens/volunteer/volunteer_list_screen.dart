import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../providers/volunteer_provider.dart';
import '../../widgets/volunteer_card.dart';
import 'register_volunteer_screen.dart';
import 'match_screen.dart';

class VolunteerListScreen extends StatefulWidget {
  const VolunteerListScreen({super.key});

  @override
  State<VolunteerListScreen> createState() => _VolunteerListScreenState();
}

class _VolunteerListScreenState extends State<VolunteerListScreen> {
  String _searchQuery = '';

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      context.read<VolunteerProvider>().fetchVolunteers();
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Volunteers'),
        actions: [
          IconButton(
            icon: const Icon(Icons.auto_awesome),
            onPressed: () => Navigator.push(context, MaterialPageRoute(builder: (_) => const MatchScreen())),
          ),
        ],
      ),
      body: Column(
        children: [
          Consumer<VolunteerProvider>(
            builder: (context, provider, child) {
              final total = provider.volunteers.length;
              final available = provider.volunteers.where((v) => v.available).length;
              return Padding(
                padding: const EdgeInsets.all(16.0),
                child: Row(
                  children: [
                    _buildMiniStat('Total', total.toString(), Colors.blue),
                    const SizedBox(width: 16),
                    _buildMiniStat('Available', available.toString(), Colors.green),
                  ],
                ),
              );
            },
          ),
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 16.0),
            child: SearchBar(
              hintText: 'Search by name, district, or skill...',
              onChanged: (value) => setState(() => _searchQuery = value),
              leading: const Icon(Icons.search),
            ),
          ),
          const SizedBox(height: 16),
          Expanded(
            child: Consumer<VolunteerProvider>(
              builder: (context, provider, child) {
                final filtered = provider.volunteers.where((v) {
                  return v.name.toLowerCase().contains(_searchQuery.toLowerCase()) ||
                         v.district.toLowerCase().contains(_searchQuery.toLowerCase()) ||
                         v.skills.any((s) => s.toLowerCase().contains(_searchQuery.toLowerCase()));
                }).toList();

                if (provider.isLoading && filtered.isEmpty) {
                  return const Center(child: CircularProgressIndicator());
                }

                return RefreshIndicator(
                  onRefresh: provider.fetchVolunteers,
                  child: ListView.builder(
                    padding: const EdgeInsets.symmetric(horizontal: 16),
                    itemCount: filtered.length,
                    itemBuilder: (context, index) {
                      return VolunteerCard(volunteer: filtered[index]);
                    },
                  ),
                );
              },
            ),
          ),
        ],
      ),
      floatingActionButton: FloatingActionButton.extended(
        onPressed: () => Navigator.push(context, MaterialPageRoute(builder: (_) => const RegisterVolunteerScreen())),
        label: const Text('Register'),
        icon: const Icon(Icons.person_add),
        backgroundColor: Colors.teal,
      ),
    );
  }

  Widget _buildMiniStat(String label, String value, Color color) {
    return Expanded(
      child: Container(
        padding: const EdgeInsets.all(12),
        decoration: BoxDecoration(
          color: color.withValues(alpha: 0.1),
          borderRadius: BorderRadius.circular(12),
          border: Border.all(color: color.withValues(alpha: 0.3)),
        ),
        child: Column(
          children: [
            Text(value, style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold, color: color)),
            Text(label, style: TextStyle(fontSize: 12, color: color.withValues(alpha: 0.8))),
          ],
        ),
      ),
    );
  }
}
