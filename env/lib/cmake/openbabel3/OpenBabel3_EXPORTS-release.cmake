#----------------------------------------------------------------
# Generated CMake target import file for configuration "Release".
#----------------------------------------------------------------

# Commands may need to know the format version.
set(CMAKE_IMPORT_FILE_VERSION 1)

# Import target "openbabel" for configuration "Release"
set_property(TARGET openbabel APPEND PROPERTY IMPORTED_CONFIGURATIONS RELEASE)
set_target_properties(openbabel PROPERTIES
  IMPORTED_LOCATION_RELEASE "${_IMPORT_PREFIX}/lib/libopenbabel.7.0.0.dylib"
  IMPORTED_SONAME_RELEASE "/Users/wenzhenxiong/Library/CloudStorage/OneDrive-Microsoft365/DNADancer/ProteinDance/env/lib/libopenbabel.7.dylib"
  )

list(APPEND _cmake_import_check_targets openbabel )
list(APPEND _cmake_import_check_files_for_openbabel "${_IMPORT_PREFIX}/lib/libopenbabel.7.0.0.dylib" )

# Import target "inchi" for configuration "Release"
set_property(TARGET inchi APPEND PROPERTY IMPORTED_CONFIGURATIONS RELEASE)
set_target_properties(inchi PROPERTIES
  IMPORTED_LOCATION_RELEASE "${_IMPORT_PREFIX}/lib/libinchi.0.4.1.dylib"
  IMPORTED_SONAME_RELEASE "/Users/wenzhenxiong/Library/CloudStorage/OneDrive-Microsoft365/DNADancer/ProteinDance/env/lib/libinchi.0.dylib"
  )

list(APPEND _cmake_import_check_targets inchi )
list(APPEND _cmake_import_check_files_for_inchi "${_IMPORT_PREFIX}/lib/libinchi.0.4.1.dylib" )

# Commands beyond this point should not need to know the version.
set(CMAKE_IMPORT_FILE_VERSION)
