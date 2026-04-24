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

  final List<String> _allSkills = ['Medical', 'Teaching', 'Logistics', 'Cooking', 'Counselling', 'Construction', 'IT Support'];
  final List<String> _selectedSkills = [];

  final List<String> _allLanguages = ['Marathi', 'Hindi', 'English', 'Kannada', 'Telugu'];
  final List<String> _selectedLanguages = [];

  final List<String> _districts = [
    'Ahmednagar', 'Akola', 'Amravati', 'Aurangabad', 'Beed', 'Bhandara', 'Buldhana', 
    'Chandrapur', 'Dhule', 'Gadchiroli', 'Gondia', 'Hingoli', 'Jalgaon', 'Jalna', 
    'Kolhapur', 'Latur', 'Mumbai City', 'Mumbai Suburban', 'Nagpur', 'Nanded', 
    'Nandurbar', 'Nashik', 'Osmanabad', 'Palghar', 'Parbhani', 'Pune', 'Raigad', 
    'Ratnagiri', 'Sangli', 'Satara', 'Sindhururg', 'Solapur', 'Thane', 'Wardha', 
    'Washim', 'Yavatmal'
  ];

  void _submit() async {
    if (_formKey.currentState!.validate()) {
      if (_selectedSkills.isEmpty) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Please select at least one skill')),
        );
        return;
      }

      final data = {
        'name': _nameController.text,
        'phone': _phoneController.text,
        'district': _district,
        'skills': _selectedSkills,
        'languages': _selectedLanguages,
        'available': _available,
        'location': {'latitude': 19.0760, 'longitude': 72.8777},
      };

      final success = await context.read<VolunteerProvider>().registerVolunteer(data);
      if (mounted) {
        if (success) {
          showDialog(
            context: context,
            builder: (context) => AlertDialog(
              title: const Text('Success'),
              content: const Text('Volunteer registered successfully!'),
              actions: [
                TextButton(onPressed: () { Navigator.pop(context); Navigator.pop(context); }, child: const Text('OK')),
              ],
            ),
          );
        } else {
          ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Registration failed.')));
        }
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFFF8FAFC),
      appBar: AppBar(
        title: const Text('Join the Mission', style: TextStyle(fontWeight: FontWeight.bold, color: Colors.white)),
        backgroundColor: Colors.teal.shade700,
        elevation: 0,
        centerTitle: true,
      ),
      body: Container(
        decoration: BoxDecoration(
          gradient: LinearGradient(
            begin: Alignment.topCenter,
            end: Alignment.bottomCenter,
            colors: [Colors.teal.shade700, const Color(0xFFF8FAFC)],
            stops: const [0.0, 0.2],
          ),
        ),
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(20),
          child: Form(
            key: _formKey,
            child: Column(
              children: [
                Card(
                  elevation: 4,
                  shadowColor: Colors.black12,
                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
                  child: Padding(
                    padding: const EdgeInsets.all(24),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        const Text('Personal Details', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold, color: Color(0xFF1E293B))),
                        const SizedBox(height: 20),
                        _buildTextField(_nameController, 'Full Name', Icons.person),
                        const SizedBox(height: 16),
                        _buildTextField(_phoneController, 'Phone Number', Icons.phone, keyboardType: TextInputType.phone),
                        const SizedBox(height: 16),
                        DropdownButtonFormField<String>(
                          value: _district,
                          decoration: _inputDecoration('District', Icons.map),
                          items: _districts.map((d) => DropdownMenuItem(value: d, child: Text(d))).toList(),
                          onChanged: (v) => setState(() => _district = v!),
                        ),
                      ],
                    ),
                  ),
                ),
                const SizedBox(height: 20),
                Card(
                  elevation: 4,
                  shadowColor: Colors.black12,
                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
                  child: Padding(
                    padding: const EdgeInsets.all(24),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        const Text('Skills & Expertise', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold, color: Color(0xFF1E293B))),
                        const SizedBox(height: 12),
                        const Text('Select all that apply', style: TextStyle(fontSize: 14, color: Colors.grey)),
                        const SizedBox(height: 16),
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
                              labelStyle: TextStyle(color: isSelected ? Colors.teal.shade800 : Colors.black87),
                            );
                          }).toList(),
                        ),
                      ],
                    ),
                  ),
                ),
                const SizedBox(height: 20),
                Card(
                  elevation: 4,
                  shadowColor: Colors.black12,
                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
                  child: SwitchListTile(
                    title: const Text('Available for immediate deployment', style: TextStyle(fontWeight: FontWeight.w500)),
                    subtitle: const Text('Receive notifications for urgent needs'),
                    value: _available,
                    activeColor: Colors.teal,
                    onChanged: (v) => setState(() => _available = v),
                  ),
                ),
                const SizedBox(height: 32),
                ElevatedButton(
                  onPressed: _submit,
                  style: ElevatedButton.styleFrom(
                    minimumSize: const Size(double.infinity, 56),
                    backgroundColor: Colors.teal.shade700,
                    foregroundColor: Colors.white,
                    shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
                    elevation: 8,
                    shadowColor: Colors.teal.withOpacity(0.4),
                  ),
                  child: const Text('Complete Registration', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
                ),
                const SizedBox(height: 20),
              ],
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildTextField(TextEditingController controller, String label, IconData icon, {TextInputType? keyboardType}) {
    return TextFormField(
      controller: controller,
      keyboardType: keyboardType,
      decoration: _inputDecoration(label, icon),
      validator: (v) => v!.isEmpty ? 'Field required' : null,
    );
  }

  InputDecoration _inputDecoration(String label, IconData icon) {
    return InputDecoration(
      labelText: label,
      prefixIcon: Icon(icon, color: Colors.teal.shade700),
      filled: true,
      fillColor: Colors.white,
      border: OutlineInputBorder(borderRadius: BorderRadius.circular(12), borderSide: BorderSide(color: Colors.grey.shade300)),
      enabledBorder: OutlineInputBorder(borderRadius: BorderRadius.circular(12), borderSide: BorderSide(color: Colors.grey.shade300)),
      focusedBorder: OutlineInputBorder(borderRadius: BorderRadius.circular(12), borderSide: BorderSide(color: Colors.teal.shade700, width: 2)),
    );
  }
}
