import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../providers/volunteer_provider.dart';
import '../../widgets/match_result_card.dart';

class MatchScreen extends StatefulWidget {
  const MatchScreen({super.key});

  @override
  State<MatchScreen> createState() => _MatchScreenState();
}

class _MatchScreenState extends State<MatchScreen> {
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('AI Volunteer Matching'),
        actions: [
          IconButton(
            icon: Icon(Icons.auto_awesome, color: Colors.purple[300]),
            onPressed: () => _showMatchingExplanation(context),
            tooltip: 'How AI Matching Works',
          ),
        ],
      ),
      body: Consumer<VolunteerProvider>(
        builder: (context, provider, child) {
          if (provider.isMatchingInProgress) {
            return Center(
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  const CircularProgressIndicator(color: Colors.purple),
                  const SizedBox(height: 24),
                  const Text('Gemini is analysing skills and needs...', style: TextStyle(fontStyle: FontStyle.italic, fontSize: 16)),
                  const SizedBox(height: 8),
                  Text('Optimising deployment for ${provider.volunteers.length} volunteers', style: const TextStyle(color: Colors.grey, fontSize: 12)),
                ],
              ),
            );
          }

          if (provider.matchResults.isEmpty) {
            return Center(
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Container(
                    padding: const EdgeInsets.all(32),
                    decoration: BoxDecoration(
                      color: Colors.purple.withOpacity(0.1),
                      shape: BoxShape.circle,
                    ),
                    child: const Icon(Icons.psychology, size: 100, color: Colors.purple),
                  ),
                  const SizedBox(height: 24),
                  const Text('Powered by Gemini AI', style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold, fontFamily: 'Poppins')),
                  const SizedBox(height: 12),
                  const Padding(
                    padding: EdgeInsets.symmetric(horizontal: 48),
                    child: Text(
                      'Match your available volunteers to the most critical community needs using AI-driven analysis.',
                      textAlign: TextAlign.center,
                      style: TextStyle(color: Colors.grey),
                    ),
                  ),
                  const SizedBox(height: 32),
                  ElevatedButton(
                    onPressed: () => provider.runMatching(),
                    style: ElevatedButton.styleFrom(
                      padding: const EdgeInsets.symmetric(horizontal: 40, vertical: 16),
                      backgroundColor: Colors.purple,
                      foregroundColor: Colors.white,
                      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(30)),
                    ),
                    child: const Text('Run Matching', style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
                  ),
                  const SizedBox(height: 16),
                  TextButton.icon(
                    onPressed: () => _showMatchingExplanation(context),
                    icon: Icon(Icons.info_outline, size: 16, color: Colors.purple[300]),
                    label: Text('How does AI matching work?', style: TextStyle(color: Colors.purple[300], fontSize: 13)),
                  ),
                ],
              ),
            );
          }

          return Column(
            children: [
              Container(
                width: double.infinity,
                padding: const EdgeInsets.all(16),
                color: Colors.purple.withOpacity(0.05),
                child: Text(
                  'Found ${provider.matchResults.length} optimal matches',
                  textAlign: TextAlign.center,
                  style: const TextStyle(color: Colors.purple, fontWeight: FontWeight.bold),
                ),
              ),
              Expanded(
                child: ListView.builder(
                  padding: const EdgeInsets.all(16),
                  itemCount: provider.matchResults.length,
                  itemBuilder: (context, index) {
                    return MatchResultCard(match: provider.matchResults[index]);
                  },
                ),
              ),
              Padding(
                padding: const EdgeInsets.all(16.0),
                child: ElevatedButton(
                  onPressed: () {
                    ScaffoldMessenger.of(context).showSnackBar(
                      SnackBar(content: Text('Notifications sent to ${provider.matchResults.length} volunteers')),
                    );
                  },
                  style: ElevatedButton.styleFrom(
                    minimumSize: const Size(double.infinity, 56),
                    backgroundColor: Colors.black,
                    foregroundColor: Colors.white,
                  ),
                  child: const Text('Notify All Volunteers'),
                ),
              ),
            ],
          );
        },
      ),
    );
  }

  /// Shows a detailed explanation of how the AI matching algorithm works
  void _showMatchingExplanation(BuildContext context) {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
      ),
      builder: (context) {
        return Padding(
          padding: const EdgeInsets.all(24),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Center(
                child: Container(
                  width: 40, height: 4,
                  decoration: BoxDecoration(color: Colors.grey[400], borderRadius: BorderRadius.circular(2)),
                ),
              ),
              const SizedBox(height: 20),
              Row(
                children: [
                  Icon(Icons.auto_awesome, color: Colors.purple[400]),
                  const SizedBox(width: 8),
                  const Text('How AI Matching Works', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
                ],
              ),
              const SizedBox(height: 16),
              const Text(
                'Our AI uses Google Gemini to intelligently match volunteers to community needs. Here\'s what it considers:',
                style: TextStyle(color: Colors.grey, fontSize: 14),
              ),
              const SizedBox(height: 20),
              _buildExplanationItem(
                '🎯', 'Skill Match (Primary)',
                'Compares volunteer skills (medical, teaching, logistics, cooking, etc.) with the category of each urgent need.',
              ),
              _buildExplanationItem(
                '📍', 'Geographic Proximity',
                'Prioritizes volunteers in the same district or nearby areas to minimize travel time and respond faster.',
              ),
              _buildExplanationItem(
                '🗣️', 'Language Compatibility',
                'Considers language match between the volunteer and the affected community for effective communication.',
              ),
              _buildExplanationItem(
                '🔥', 'Need Urgency',
                'Higher urgency needs (based on severity, affected count) get matched to the most qualified volunteers first.',
              ),
              _buildExplanationItem(
                '⭐', 'Match Score',
                'A confidence percentage combining all factors. Higher scores indicate stronger, more reliable matches.',
              ),
              const SizedBox(height: 16),
            ],
          ),
        );
      },
    );
  }

  Widget _buildExplanationItem(String emoji, String title, String description) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 14),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(emoji, style: const TextStyle(fontSize: 20)),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(title, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 14)),
                const SizedBox(height: 2),
                Text(description, style: const TextStyle(color: Colors.grey, fontSize: 13)),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
