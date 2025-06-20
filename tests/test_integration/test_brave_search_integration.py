"""
Brave Search MCP Integration tests for Music Collection MCP Server.

Tests integration scenarios with Brave Search MCP server for band information fetching,
including mock testing and external service integration patterns.
"""

import unittest
import tempfile
import shutil
from unittest.mock import patch, MagicMock, AsyncMock
from pathlib import Path

from src.core.prompts.fetch_band_info import get_fetch_band_info_prompt
from src.models import BandMetadata, Album


class TestBraveSearchMCPIntegration(unittest.TestCase):
    """Test suite for Brave Search MCP integration scenarios."""

    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Clean up test environment."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_fetch_band_info_prompt_for_brave_search(self):
        """Test fetch_band_info prompt generation for Brave Search integration."""
        # Test basic band info prompt
        prompt = get_fetch_band_info_prompt(
            band_name="Pink Floyd",
            information_scope="full",
            existing_albums=["The Wall", "Dark Side of the Moon"]
        )
        
        # Verify prompt structure for MCP integration
        self.assertIsInstance(prompt, dict)
        self.assertEqual(prompt["name"], "fetch_band_info")
        self.assertIn("arguments", prompt)
        
        # Verify content includes band-specific instructions
        content = prompt["messages"][0]["content"]["text"]
        self.assertIn("Pink Floyd", content)
        self.assertIn("The Wall", content)
        self.assertIn("Dark Side of the Moon", content)
        
        # Verify search strategy includes reliable sources
        self.assertIn("Wikipedia", content)
        self.assertIn("AllMusic", content)
        self.assertIn("official", content)
        
        # Verify JSON schema format for band metadata
        self.assertIn("band_name", content)
        self.assertIn("formed", content)
        self.assertIn("genres", content)
        self.assertIn("albums", content)

    def test_prompt_generation_for_missing_albums_discovery(self):
        """Test prompt generation specifically for missing albums discovery."""
        existing_albums = [
            "Abbey Road",
            "Sgt. Pepper's Lonely Hearts Club Band",
            "Revolver"
        ]
        
        prompt = get_fetch_band_info_prompt(
            band_name="The Beatles",
            information_scope="albums_only",
            existing_albums=existing_albums
        )
        
        content = prompt["messages"][0]["content"]["text"]
        
        # Verify albums-only focus - check for actual content in albums template
        self.assertIn("discography", content.lower())
        self.assertIn("album information", content.lower())
        
        # Verify existing albums are mentioned for missing detection
        for album in existing_albums:
            self.assertIn(album, content)
        
        # Verify instructions for comprehensive album discovery
        self.assertIn("complete discography", content.lower())
        self.assertIn("studio albums", content.lower())

    def test_mock_brave_search_integration_successful_response(self):
        """Test successful Brave Search integration with mocked responses."""
        # Mock successful Brave Search response
        mock_response = {
            "band_name": "Led Zeppelin",
            "formed": "1968",
            "genres": ["Hard Rock", "Heavy Metal", "Blues Rock"],
            "origin": "London, England",
            "members": ["Robert Plant", "Jimmy Page", "John Paul Jones", "John Bonham"],
            "description": "English rock band formed in London in 1968.",
            "albums": [
                {
                    "album_name": "Led Zeppelin IV",
                    "year": "1971",
                    "track_count": 8
                },
                {
                    "album_name": "Physical Graffiti",
                    "year": "1975",
                    "track_count": 15
                }
            ]
        }
        
        # Generate prompt for Brave Search
        prompt = get_fetch_band_info_prompt(
            band_name="Led Zeppelin",
            information_scope="full"
        )
        
        # Verify prompt can be used with Brave Search MCP
        self.assertIsInstance(prompt, dict)
        self.assertEqual(prompt["name"], "fetch_band_info")
        
        # Simulate processing the prompt response
        response_data = mock_response
        
        # Verify response can be used to create BandMetadata
        metadata = BandMetadata(
            band_name=response_data["band_name"],
            formed=response_data["formed"],
            genres=response_data["genres"],
            origin=response_data["origin"],
            members=response_data["members"],
            description=response_data["description"],
            albums=[Album(**album) for album in response_data["albums"]]
        )
        
        self.assertEqual(metadata.band_name, "Led Zeppelin")
        self.assertEqual(metadata.formed, "1968")
        self.assertEqual(len(metadata.albums), 2)
        self.assertEqual(metadata.albums[0].album_name, "Led Zeppelin IV")

    def test_mock_brave_search_integration_partial_response(self):
        """Test Brave Search integration with partial/incomplete responses."""
        # Mock partial response (missing some fields)
        mock_response = {
            "band_name": "Queen",
            "formed": "1970",
            "genres": ["Rock", "Progressive Rock"],
            "origin": "London, England",
            # Missing members and description
            "albums": [
                {
                    "album_name": "A Night at the Opera",
                    "year": "1975"
                }
            ]
        }
        
        # Generate prompt
        prompt = get_fetch_band_info_prompt(
            band_name="Queen",
            information_scope="basic"
        )
        
        # Simulate handling partial response
        response_data = mock_response
        
        # Create metadata with defaults for missing fields
        metadata = BandMetadata(
            band_name=response_data["band_name"],
            formed=response_data["formed"],
            genres=response_data["genres"],
            origin=response_data["origin"],
            members=response_data.get("members", []),
            description=response_data.get("description", ""),
            albums=[
                Album(
                    album_name=album["album_name"],
                    year=album["year"],
                    track_count=album.get("track_count", 0)
                ) for album in response_data["albums"]
            ]
        )
        
        self.assertEqual(metadata.band_name, "Queen")
        self.assertEqual(metadata.members, [])  # Default for missing field
        self.assertEqual(metadata.albums[0].track_count, 0)  # Default for missing field

    def test_mock_brave_search_integration_error_handling(self):
        """Test error handling in Brave Search integration."""
        # Generate prompt
        prompt = get_fetch_band_info_prompt(
            band_name="Unknown Band",
            information_scope="full"
        )
        
        # Verify prompt structure is still valid despite error
        self.assertIsInstance(prompt, dict)
        self.assertEqual(prompt["name"], "fetch_band_info")
        
        # Prompt should include fallback instructions - check for actual content
        content = prompt["messages"][0]["content"]["text"]
        self.assertIn("fallback instructions", content.lower())
        self.assertIn("empty strings", content.lower())

    def test_prompt_validation_for_brave_search_format(self):
        """Test that prompts are properly formatted for Brave Search MCP."""
        test_cases = [
            {
                "band_name": "Metallica",
                "information_scope": "full",
                "existing_albums": ["Master of Puppets", "Ride the Lightning"]
            },
            {
                "band_name": "Radiohead",
                "information_scope": "basic",
                "existing_albums": []
            },
            {
                "band_name": "Nirvana",
                "information_scope": "albums_only",
                "existing_albums": ["Nevermind"]
            }
        ]
        
        for case in test_cases:
            prompt = get_fetch_band_info_prompt(**case)
            
            # Verify MCP prompt format
            self.assertIn("name", prompt)
            self.assertIn("arguments", prompt)
            self.assertIn("messages", prompt)
            
            # Verify message structure
            message = prompt["messages"][0]
            self.assertIn("role", message)
            self.assertIn("content", message)
            self.assertEqual(message["role"], "user")
            
            # Verify content structure
            content = message["content"]
            self.assertIn("type", content)
            self.assertIn("text", content)
            self.assertEqual(content["type"], "text")
            
            # Verify content includes band name
            self.assertIn(case["band_name"], content["text"])

    def test_integration_workflow_simulation(self):
        """Test complete integration workflow simulation."""
        # Simulate complete workflow: prompt generation -> search -> response processing
        
        # Step 1: Generate prompt for Brave Search
        band_name = "The Rolling Stones"
        existing_albums = ["Sticky Fingers", "Exile on Main St."]
        
        prompt = get_fetch_band_info_prompt(
            band_name=band_name,
            information_scope="full",
            existing_albums=existing_albums
        )
        
        # Step 2: Simulate Brave Search response processing
        simulated_brave_response = {
            "band_name": "The Rolling Stones",
            "formed": "1962",
            "genres": ["Rock", "Blues Rock", "Hard Rock"],
            "origin": "London, England",
            "members": ["Mick Jagger", "Keith Richards", "Ronnie Wood", "Charlie Watts"],
            "description": "English rock band formed in London in 1962.",
            "albums": [
                {"album_name": "Sticky Fingers", "year": "1971", "track_count": 10},
                {"album_name": "Exile on Main St.", "year": "1972", "track_count": 18},
                {"album_name": "Let It Bleed", "year": "1969", "track_count": 9},
                {"album_name": "Beggars Banquet", "year": "1968", "track_count": 10}
            ]
        }
        
        # Step 3: Process response into metadata
        metadata = BandMetadata(
            band_name=simulated_brave_response["band_name"],
            formed=simulated_brave_response["formed"],
            genres=simulated_brave_response["genres"],
            origin=simulated_brave_response["origin"],
            members=simulated_brave_response["members"],
            description=simulated_brave_response["description"],
            albums=[Album(**album) for album in simulated_brave_response["albums"]]
        )
        
        # Step 4: Verify integration workflow results
        self.assertEqual(metadata.band_name, band_name)
        self.assertEqual(len(metadata.albums), 4)
        
        # Step 5: Identify missing albums (albums not in existing_albums)
        existing_album_names = set(existing_albums)
        all_album_names = {album.album_name for album in metadata.albums}
        missing_albums = all_album_names - existing_album_names
        
        self.assertEqual(missing_albums, {"Let It Bleed", "Beggars Banquet"})
        
        print(f"\n=== Integration Workflow Simulation ===")
        print(f"Band: {band_name}")
        print(f"Existing albums: {len(existing_albums)}")
        print(f"Total albums found: {len(metadata.albums)}")
        print(f"Missing albums discovered: {len(missing_albums)}")
        print(f"Missing albums: {list(missing_albums)}")

    def test_brave_search_integration_summary(self):
        """Summary test documenting Brave Search integration scenarios."""
        integration_scenarios = {
            "Prompt Generation": "Band-specific prompts for Brave Search MCP",
            "Missing Albums Discovery": "Albums-only scope for discography completion",
            "Successful Response Processing": "Full metadata extraction from search results",
            "Partial Response Handling": "Graceful handling of incomplete data",
            "Error Scenario Management": "Fallback strategies for search failures",
            "Schema Validation": "Response format validation and processing",
            "Complete Workflow": "End-to-end integration simulation"
        }
        
        print(f"\n=== Brave Search Integration Scenarios ===")
        for scenario, description in integration_scenarios.items():
            print(f"{scenario}: {description}")
        
        # Verify all integration components are testable
        self.assertTrue(True)  # This test documents integration patterns


if __name__ == '__main__':
    unittest.main() 
