import 'package:flutter/material.dart';
import '../models/survey.dart';
import 'urgency_badge.dart';
import 'package:intl/intl.dart';

class SurveyCard extends StatelessWidget {
  final Survey survey;

  const SurveyCard({super.key, required this.survey});

  @override
  Widget build(BuildContext context) {
    return Card(
      margin: const EdgeInsets.only(bottom: 12),
      clipBehavior: Clip.antiAlias,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
      child: Container(
        decoration: BoxDecoration(
          border: Border(left: BorderSide(color: survey.categoryColor, width: 4)),
        ),
        child: Padding(
          padding: const EdgeInsets.all(16.0),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                children: [
                  Text(survey.categoryEmoji, style: const TextStyle(fontSize: 18)),
                  const SizedBox(width: 8),
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                    decoration: BoxDecoration(
                      color: survey.categoryColor.withValues(alpha: 0.1),
                      borderRadius: BorderRadius.circular(20),
                    ),
                    child: Text(
                      survey.category.toUpperCase(),
                      style: TextStyle(color: survey.categoryColor, fontWeight: FontWeight.bold, fontSize: 10),
                    ),
                  ),
                  const Spacer(),
                  UrgencyBadge(score: survey.urgencyScore),
                ],
              ),
              const SizedBox(height: 12),
              Text(
                survey.description,
                maxLines: 2,
                overflow: TextOverflow.ellipsis,
                style: const TextStyle(fontWeight: FontWeight.w500, fontSize: 14),
              ),
              const SizedBox(height: 12),
              Row(
                children: [
                  const Icon(Icons.location_on, size: 14, color: Colors.grey),
                  const SizedBox(width: 4),
                  Text(survey.district, style: const TextStyle(color: Colors.grey, fontSize: 12)),
                  const SizedBox(width: 12),
                  const Icon(Icons.calendar_today, size: 14, color: Colors.grey),
                  const SizedBox(width: 4),
                  Text(
                    DateFormat('dd MMM').format(survey.submittedAt),
                    style: const TextStyle(color: Colors.grey, fontSize: 12),
                  ),
                  const Spacer(),
                  Row(
                    children: List.generate(5, (index) {
                      return Icon(
                        Icons.circle,
                        size: 8,
                        color: index < survey.severity ? Colors.red : Colors.grey[300],
                      );
                    }),
                  ),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }
}
