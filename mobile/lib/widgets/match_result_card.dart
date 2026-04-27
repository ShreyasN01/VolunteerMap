import 'package:flutter/material.dart';
import '../models/match_result.dart';

class MatchResultCard extends StatelessWidget {
  final MatchResult match;

  const MatchResultCard({super.key, required this.match});

  @override
  Widget build(BuildContext context) {
    return Card(
      margin: const EdgeInsets.only(bottom: 16),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                CircleAvatar(
                  backgroundColor: _getAvatarColor(match.volunteerName),
                  child: Text(match.volunteerName[0], style: const TextStyle(color: Colors.white)),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(match.volunteerName, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
                      Text(
                        match.needCategory.isNotEmpty ? match.needCategory.toUpperCase() : 'GENERAL',
                        style: const TextStyle(fontSize: 12, color: Colors.grey, fontWeight: FontWeight.bold),
                      ),
                    ],
                  ),
                ),
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                  decoration: BoxDecoration(
                    color: match.priorityColor.withOpacity(0.1),
                    borderRadius: BorderRadius.circular(12),
                  ),
                  child: Text(
                    match.priority[0].toUpperCase() + match.priority.substring(1),
                    style: TextStyle(color: match.priorityColor, fontSize: 10, fontWeight: FontWeight.bold),
                  ),
                ),
              ],
            ),
            const Divider(height: 24),

            // Match Reason
            const Text('Match Reason:', style: TextStyle(fontSize: 12, fontWeight: FontWeight.bold, color: Colors.grey)),
            const SizedBox(height: 4),
            Text(
              match.matchReason,
              style: const TextStyle(fontStyle: FontStyle.italic, fontSize: 13),
            ),
            const SizedBox(height: 12),

            // AI Matching Basis explanation
            Container(
              width: double.infinity,
              padding: const EdgeInsets.all(10),
              decoration: BoxDecoration(
                color: Colors.purple.withOpacity(0.05),
                borderRadius: BorderRadius.circular(8),
                border: Border.all(color: Colors.purple.withOpacity(0.15)),
              ),
              child: Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Icon(Icons.auto_awesome, size: 14, color: Colors.purple[300]),
                  const SizedBox(width: 6),
                  Expanded(
                    child: Text(
                      match.matchBasis,
                      style: TextStyle(fontSize: 11, color: Colors.purple[200], fontWeight: FontWeight.w500),
                    ),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 12),

            // Chips and View Need button
            Row(
              children: [
                _buildChip(Icons.straighten, '${match.distance.toStringAsFixed(1)} km', Colors.blue),
                const SizedBox(width: 8),
                _buildChip(Icons.star, '${(match.matchScore * 100).toInt()}% Match', Colors.orange),
                const Spacer(),
                TextButton(
                  onPressed: () => _showNeedDetails(context),
                  child: const Text('View Need'),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }

  /// Shows a dialog with full details about the matched community need
  void _showNeedDetails(BuildContext context) {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
      ),
      builder: (context) {
        return DraggableScrollableSheet(
          initialChildSize: 0.5,
          minChildSize: 0.3,
          maxChildSize: 0.8,
          expand: false,
          builder: (context, scrollController) {
            return SingleChildScrollView(
              controller: scrollController,
              padding: const EdgeInsets.all(24),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  // Drag handle
                  Center(
                    child: Container(
                      width: 40,
                      height: 4,
                      decoration: BoxDecoration(
                        color: Colors.grey[400],
                        borderRadius: BorderRadius.circular(2),
                      ),
                    ),
                  ),
                  const SizedBox(height: 20),

                  // Title
                  Row(
                    children: [
                      Icon(_getCategoryIcon(), color: _getCategoryColor(), size: 28),
                      const SizedBox(width: 12),
                      Expanded(
                        child: Text(
                          'Need Details',
                          style: const TextStyle(fontSize: 20, fontWeight: FontWeight.bold),
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 20),

                  // Category
                  _buildDetailRow('Category', match.needCategory.isNotEmpty
                      ? match.needCategory[0].toUpperCase() + match.needCategory.substring(1)
                      : 'Not specified'),
                  _buildDetailRow('District', match.needDistrict.isNotEmpty ? match.needDistrict : 'Not specified'),
                  _buildDetailRow('Priority', match.priority[0].toUpperCase() + match.priority.substring(1)),
                  _buildDetailRow('Need ID', match.needId),
                  const SizedBox(height: 16),

                  // Task Summary
                  const Text('Task Summary', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 14, color: Colors.grey)),
                  const SizedBox(height: 6),
                  Text(match.taskSummary.isNotEmpty ? match.taskSummary : match.matchReason,
                      style: const TextStyle(fontSize: 14)),
                  const SizedBox(height: 20),

                  // Assigned Volunteer
                  const Text('Assigned Volunteer', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 14, color: Colors.grey)),
                  const SizedBox(height: 8),
                  Container(
                    padding: const EdgeInsets.all(12),
                    decoration: BoxDecoration(
                      color: Colors.teal.withOpacity(0.08),
                      borderRadius: BorderRadius.circular(12),
                      border: Border.all(color: Colors.teal.withOpacity(0.2)),
                    ),
                    child: Row(
                      children: [
                        CircleAvatar(
                          backgroundColor: _getAvatarColor(match.volunteerName),
                          radius: 20,
                          child: Text(match.volunteerName[0], style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold)),
                        ),
                        const SizedBox(width: 12),
                        Expanded(
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text(match.volunteerName, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 15)),
                              const SizedBox(height: 4),
                              Row(
                                children: [
                                  _buildChip(Icons.straighten, '${match.distance.toStringAsFixed(1)} km', Colors.blue),
                                  const SizedBox(width: 8),
                                  _buildChip(Icons.star, '${(match.matchScore * 100).toInt()}%', Colors.orange),
                                ],
                              ),
                            ],
                          ),
                        ),
                      ],
                    ),
                  ),
                  const SizedBox(height: 20),

                  // AI Matching Explanation
                  const Text('How AI Matched', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 14, color: Colors.grey)),
                  const SizedBox(height: 8),
                  Container(
                    width: double.infinity,
                    padding: const EdgeInsets.all(14),
                    decoration: BoxDecoration(
                      color: Colors.purple.withOpacity(0.06),
                      borderRadius: BorderRadius.circular(12),
                      border: Border.all(color: Colors.purple.withOpacity(0.15)),
                    ),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Row(
                          children: [
                            Icon(Icons.auto_awesome, size: 16, color: Colors.purple[300]),
                            const SizedBox(width: 6),
                            const Text('Gemini AI Analysis', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 13)),
                          ],
                        ),
                        const SizedBox(height: 10),
                        _buildFactorRow('🎯 Skill Match', 'Volunteer skills aligned with the need category'),
                        _buildFactorRow('📍 Proximity', '${match.distance.toStringAsFixed(1)} km from the need location'),
                        _buildFactorRow('⭐ Match Score', '${(match.matchScore * 100).toInt()}% confidence'),
                        _buildFactorRow('🔥 Priority', '${match.priority[0].toUpperCase()}${match.priority.substring(1)} urgency level'),
                        const SizedBox(height: 8),
                        Text(
                          match.matchReason,
                          style: TextStyle(fontSize: 12, fontStyle: FontStyle.italic, color: Colors.grey[400]),
                        ),
                      ],
                    ),
                  ),
                  const SizedBox(height: 24),
                ],
              ),
            );
          },
        );
      },
    );
  }

  Widget _buildDetailRow(String label, String value) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 6),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          SizedBox(
            width: 90,
            child: Text(label, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 13, color: Colors.grey)),
          ),
          Expanded(child: Text(value, style: const TextStyle(fontSize: 14))),
        ],
      ),
    );
  }

  Widget _buildFactorRow(String emoji, String description) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 3),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(emoji, style: const TextStyle(fontSize: 13)),
          const SizedBox(width: 8),
          Expanded(child: Text(description, style: const TextStyle(fontSize: 12))),
        ],
      ),
    );
  }

  Widget _buildChip(IconData icon, String label, Color color) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
      decoration: BoxDecoration(color: color.withOpacity(0.1), borderRadius: BorderRadius.circular(8)),
      child: Row(
        children: [
          Icon(icon, size: 12, color: color),
          const SizedBox(width: 4),
          Text(label, style: TextStyle(color: color, fontSize: 10, fontWeight: FontWeight.bold)),
        ],
      ),
    );
  }

  IconData _getCategoryIcon() {
    switch (match.needCategory.toLowerCase()) {
      case 'healthcare': return Icons.local_hospital;
      case 'food': return Icons.restaurant;
      case 'education': return Icons.school;
      case 'sanitation': return Icons.water_drop;
      case 'employment': return Icons.work;
      default: return Icons.help_outline;
    }
  }

  Color _getCategoryColor() {
    switch (match.needCategory.toLowerCase()) {
      case 'healthcare': return const Color(0xFFEF5350);
      case 'food': return const Color(0xFFFFA726);
      case 'education': return const Color(0xFF42A5F5);
      case 'sanitation': return const Color(0xFF66BB6A);
      case 'employment': return const Color(0xFFAB47BC);
      default: return Colors.teal;
    }
  }

  Color _getAvatarColor(String name) {
    final int hash = name.hashCode;
    final List<Color> colors = [Colors.teal, Colors.blue, Colors.purple, Colors.orange, Colors.indigo];
    return colors[hash.abs() % colors.length];
  }
}
