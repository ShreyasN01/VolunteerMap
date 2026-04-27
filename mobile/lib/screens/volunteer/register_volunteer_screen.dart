import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../providers/volunteer_provider.dart';

class RegisterVolunteerScreen extends StatefulWidget {
  const RegisterVolunteerScreen({super.key});

  @override
  State<RegisterVolunteerScreen> createState() => _RegisterVolunteerScreenState();
}

class _RegisterVolunteerScreenState extends State<RegisterVolunteerScreen> {
  final _formKey = GlobalKey<FormState>();
  final TextEditingController _nameController = TextEditingController();
  final TextEditingController _phoneController = TextEditingController();
  String _district = 'Pune';
  bool _available = true;
  bool _isSubmitting = false;

  final List<String> _allSkills = ['Medical', 'Teaching', 'Logistics', 'Cooking', 'Counselling', 'Construction', 'IT Support'];
  final List<String> _selectedSkills = [];

  final List<String> _allLanguages = ['Marathi', 'Hindi', 'English', 'Kannada', 'Telugu'];
  final List<String> _selectedLanguages = ['Hindi', 'English'];

  final List<String> _districts = [
    'Ahmednagar', 'Akola', 'Amravati', 'Aurangabad', 'Beed', 'Bhandara', 'Buldhana', 
    'Chandrapur', 'Dhule', 'Gadchiroli', 'Gondia', 'Hingoli', 'Jalgaon', 'Jalna', 
    'Kolhapur', 'Latur', 'Mumbai City', 'Mumbai Suburban', 'Nagpur', 'Nanded', 
    'Nandurbar', 'Nashik', 'Osmanabad', 'Palghar', 'Parbhani', 'Pune', 'Raigad', 
    'Ratnagiri', 'Sangli', 'Satara', 'Sindhururg', 'Solapur', 'Thane', 'Wardha', 
    'Washim', 'Yavatmal'
  ];

  // District to approximate location mapping
  final Map<String, Map<String, double>> _districtCoords = {
    'Pune': {'latitude': 18.5204, 'longitude': 73.8567},
    'Mumbai City': {'latitude': 19.0760, 'longitude': 72.8777},
    'Mumbai Suburban': {'latitude': 19.1136, 'longitude': 72.8697},
    'Nashik': {'latitude': 19.9975, 'longitude': 73.7898},
    'Nagpur': {'latitude': 21.1458, 'longitude': 79.0882},
    'Kolhapur': {'latitude': 16.7050, 'longitude': 74.2433},
    'Solapur': {'latitude': 17.6599, 'longitude': 75.9064},
    'Sangli': {'latitude': 16.8524, 'longitude': 74.5815},
    'Aurangabad': {'latitude': 19.8762, 'longitude': 75.3433},
    'Thane': {'latitude': 19.2183, 'longitude': 72.9781},
  };

  void _submit() async {
    if (_formKey.currentState!.validate()) {
      if (_selectedSkills.isEmpty) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Please select at least one skill')),
        );
        return;
      }

      setState(() => _isSubmitting = true);

      // Use district-based coordinates or default
      final coords = _districtCoords[_district] ?? {'latitude': 19.0760, 'longitude': 72.8777};

      final data = {
        'name': _nameController.text.trim(),
        'phone': _phoneController.text.trim(),
        'district': _district,
        'skills': _selectedSkills.map((s) => s.toLowerCase()).toList(),
        'languages': _selectedLanguages.isNotEmpty ? _selectedLanguages : ['Hindi', 'English'],
        'available': _available,
        'location': coords,
      };

      final success = await context.read<VolunteerProvider>().registerVolunteer(data);
      
      if (mounted) {
        setState(() => _isSubmitting = false);
        if (success) {
          showDialog(
            context: context,
            builder: (context) => AlertDialog(
              title: Row(
                children: [
                  Icon(Icons.check_circle, color: Colors.green[600], size: 28),
                  const SizedBox(width: 8),
                  const Text('Success'),
                ],
              ),
              content: const Text('Volunteer registered successfully! You will be notified when matched to urgent needs.'),
              actions: [
                TextButton(
                  onPressed: () { Navigator.pop(context); Navigator.pop(context); },
                  child: const Text('OK'),
                ),
              ],
            ),
          );
        } else {
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(
              content: Text('Registration failed. Please check your connection and try again.'),
              backgroundColor: Colors.red,
            ),
          );
        }
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Register Volunteer', style: TextStyle(fontWeight: FontWeight.bold)),
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(20),
        child: Form(
          key: _formKey,
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // Personal Details
              TextFormField(
                controller: _nameController,
                decoration: _inputDecoration('Full Name', Icons.person),
                validator: (v) => (v == null || v.trim().isEmpty) ? 'Name is required' : null,
              ),
              const SizedBox(height: 16),
              TextFormField(
                controller: _phoneController,
                keyboardType: TextInputType.phone,
                decoration: _inputDecoration('Phone Number', Icons.phone),
                validator: (v) {
                  if (v == null || v.trim().isEmpty) return 'Phone number is required';
                  if (v.trim().length < 10) return 'Enter a valid phone number';
                  return null;
                },
              ),
              const SizedBox(height: 24),

              // Skills Section
              const Text('Skills', style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
              const SizedBox(height: 12),
              Wrap(
                spacing: 8,
                runSpacing: 8,
                children: _allSkills.map((skill) {
                  final isSelected = _selectedSkills.contains(skill);
                  return FilterChip(
                    label: Text(skill),
                    selected: isSelected,
                    onSelected: (val) {
                      setState(() {
                        val ? _selectedSkills.add(skill) : _selectedSkills.remove(skill);
                      });
                    },
                    selectedColor: Colors.teal.withOpacity(0.2),
                    checkmarkColor: Colors.teal,
                    labelStyle: TextStyle(
                      color: isSelected ? Colors.teal : null,
                      fontWeight: isSelected ? FontWeight.bold : FontWeight.normal,
                    ),
                  );
                }).toList(),
              ),
              const SizedBox(height: 24),

              // Languages Section
              const Text('Languages', style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
              const SizedBox(height: 12),
              Wrap(
                spacing: 8,
                runSpacing: 8,
                children: _allLanguages.map((lang) {
                  final isSelected = _selectedLanguages.contains(lang);
                  return FilterChip(
                    label: Text(lang),
                    selected: isSelected,
                    onSelected: (val) {
                      setState(() {
                        val ? _selectedLanguages.add(lang) : _selectedLanguages.remove(lang);
                      });
                    },
                    selectedColor: Colors.teal.withOpacity(0.2),
                    checkmarkColor: Colors.teal,
                    labelStyle: TextStyle(
                      color: isSelected ? Colors.teal : null,
                      fontWeight: isSelected ? FontWeight.bold : FontWeight.normal,
                    ),
                  );
                }).toList(),
              ),
              const SizedBox(height: 24),

              // District Dropdown
              DropdownButtonFormField<String>(
                value: _district,
                decoration: _inputDecoration('District', Icons.map),
                items: _districts.map((d) => DropdownMenuItem(value: d, child: Text(d))).toList(),
                onChanged: (v) => setState(() => _district = v!),
              ),
              const SizedBox(height: 24),

              // Availability Toggle
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  const Text('Available now', style: TextStyle(fontSize: 16)),
                  Switch(
                    value: _available,
                    activeColor: Colors.teal,
                    onChanged: (v) => setState(() => _available = v),
                  ),
                ],
              ),
              const SizedBox(height: 32),

              // Register Button
              SizedBox(
                width: double.infinity,
                height: 56,
                child: ElevatedButton(
                  onPressed: _isSubmitting ? null : _submit,
                  style: ElevatedButton.styleFrom(
                    backgroundColor: Colors.teal,
                    foregroundColor: Colors.white,
                    shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
                    elevation: 4,
                  ),
                  child: _isSubmitting
                      ? const SizedBox(
                          height: 24,
                          width: 24,
                          child: CircularProgressIndicator(color: Colors.white, strokeWidth: 2),
                        )
                      : const Text('Register', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
                ),
              ),
              const SizedBox(height: 20),
            ],
          ),
        ),
      ),
    );
  }

  InputDecoration _inputDecoration(String label, IconData icon) {
    return InputDecoration(
      labelText: label,
      prefixIcon: Icon(icon, color: Colors.teal),
      border: OutlineInputBorder(borderRadius: BorderRadius.circular(12)),
      enabledBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(12),
        borderSide: BorderSide(color: Colors.grey.shade400),
      ),
      focusedBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(12),
        borderSide: const BorderSide(color: Colors.teal, width: 2),
      ),
    );
  }
}
