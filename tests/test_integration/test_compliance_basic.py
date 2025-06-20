"""
Basic test for compliance validation to verify core functionality.
"""

from src.models.compliance import ComplianceValidator, ComplianceLevel
from src.models.band import Album, AlbumType

def test_basic_compliance():
    """Test basic compliance validation functionality."""
    
    # Test basic compliance functionality
    validator = ComplianceValidator()

    # Test a good album
    album = Album(
        album_name='Test Album',
        year='2020',
        type=AlbumType.ALBUM,
        folder_path='2020 - Test Album'
    )

    compliance = validator.validate_album_compliance(album, 'default')
    print(f'✅ Compliance Score: {compliance.compliance_score}')
    print(f'✅ Compliance Level: {compliance.get_compliance_level()}')
    print(f'✅ Has Year Prefix: {compliance.has_year_prefix}')
    print(f'✅ Is Compliant: {compliance.is_compliant()}')

    # Test band compliance
    albums = [album]
    report = validator.validate_band_compliance(albums, 'Test Band', 'default')
    print(f'✅ Band Report Generated: {report.band_name}')
    print(f'✅ Band Compliance Score: {report.overall_compliance_score}')
    print('✅ Task 6.4: Folder Structure Compliance and Validation - WORKING!')
    
    # Basic assertions
    assert compliance.compliance_score > 0
    assert compliance.has_year_prefix is True
    assert report.band_name == 'Test Band'
    assert report.total_albums == 1
    
    print("✅ Basic compliance validation is working!")

if __name__ == "__main__":
    test_basic_compliance() 
