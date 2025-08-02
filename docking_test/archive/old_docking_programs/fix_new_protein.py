#!/usr/bin/env python3
"""
Fix new protein structure file by removing ROOT/ENDROOT tags
"""

def fix_protein_structure(input_file, output_file):
    """Remove ROOT/ENDROOT tags from protein structure file"""
    
    print(f"🔧 Processing {input_file}...")
    
    try:
        with open(input_file, 'r') as f:
            lines = f.readlines()
        
        print(f"📖 Read {len(lines)} lines from input file")
        
        # Filter out ROOT/ENDROOT/BRANCH/ENDBRANCH/TORSDOF lines
        filtered_lines = []
        removed_lines = 0
        
        for line in lines:
            # Skip problematic lines
            if (line.strip().startswith('ROOT') or 
                line.strip().startswith('ENDROOT') or
                line.strip().startswith('BRANCH') or
                line.strip().startswith('ENDBRANCH') or
                line.strip().startswith('TORSDOF')):
                removed_lines += 1
                continue
            
            filtered_lines.append(line)
        
        print(f"🗑️ Removed {removed_lines} problematic lines")
        print(f"✅ Kept {len(filtered_lines)} valid lines")
        
        # Write cleaned file
        with open(output_file, 'w') as f:
            f.writelines(filtered_lines)
        
        print(f"💾 Cleaned file saved as: {output_file}")
        
        # Verify the result
        with open(output_file, 'r') as f:
            clean_lines = f.readlines()
        
        # Count atoms
        atom_count = sum(1 for line in clean_lines if line.startswith('ATOM') or line.startswith('HETATM'))
        print(f"🔍 Verification: {atom_count} atoms in cleaned file")
        
        # Check for remaining ROOT tags
        root_count = sum(1 for line in clean_lines if 'ROOT' in line)
        if root_count == 0:
            print("✅ No ROOT tags remaining - file is clean!")
        else:
            print(f"⚠️ Warning: {root_count} ROOT tags still present")
        
        return True
        
    except FileNotFoundError:
        print(f"❌ File not found: {input_file}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    """Main function"""
    
    print("🧬 Protein Structure File Cleaner")
    print("=" * 40)
    
    input_file = "protein_structure.pdbqt"
    output_file = "protein_receptor.pdbqt"
    
    print(f"📁 Input: {input_file}")
    print(f"📁 Output: {output_file}")
    print()
    
    if fix_protein_structure(input_file, output_file):
        print()
        print("🎉 Protein structure file successfully cleaned!")
        print("✅ Now you can run the docking with the cleaned file")
        print()
        print("Next steps:")
        print("1. Run: python vina_test_fixed.py")
        print("2. Or run: ./run_docking.sh")
    else:
        print()
        print("❌ Failed to clean protein structure file")
        return False
    
    return True

if __name__ == "__main__":
    main()