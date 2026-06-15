import os
import logging
import requests
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class LinkedInAPI:
    """
    Wrapper for the LinkedIn API to automate posting text and media.
    Requires w_member_social and r_liteprofile (or openid/profile) API scopes.
    """
    BASE_URL = "https://api.linkedin.com/v2"

    def __init__(self, access_token: Optional[str] = None):
        self.access_token = access_token or os.getenv("LINKEDIN_ACCESS_TOKEN")
        if not self.access_token:
            logger.warning("LinkedInAPI: No access token provided. API calls will fail.")
            
        self.headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
            "X-Restli-Protocol-Version": "2.0.0"
        }
        self._urn: Optional[str] = None

    def get_my_profile_urn(self) -> str:
        """
        Retrieves the authenticated user's URN (e.g., 'urn:li:person:xxxxxx').
        Supports both older /me endpoint (Lite Profile) and newer /userinfo endpoint (OIDC).
        """
        if self._urn:
            return self._urn

        if not self.access_token:
            raise ValueError("Access token is required to fetch profile URN.")

        # Try OIDC endpoint first (standard for modern LinkedIn OAuth)
        try:
            logger.info("Attempting to fetch URN from /userinfo (OIDC)...")
            response = requests.get(
                "https://api.linkedin.com/v2/userinfo", 
                headers={"Authorization": f"Bearer {self.access_token}"}
            )
            if response.status_code == 200:
                data = response.json()
                # OIDC returns 'sub' which is the unique identifier
                sub = data.get("sub")
                if sub:
                    self._urn = f"urn:li:person:{sub}"
                    logger.info(f"Retrieved profile URN from OIDC: {self._urn}")
                    return self._urn
        except Exception as e:
            logger.debug(f"OIDC lookup failed or returned error: {e}")

        # Fallback to legacy /me endpoint
        logger.info("Attempting to fetch URN from legacy /me endpoint...")
        response = requests.get(f"{self.BASE_URL}/me", headers=self.headers)
        if response.status_code == 200:
            data = response.json()
            user_id = data.get("id")
            if user_id:
                self._urn = f"urn:li:person:{user_id}"
                logger.info(f"Retrieved profile URN from /me: {self._urn}")
                return self._urn
        
        raise Exception(
            f"Failed to fetch profile URN from LinkedIn. "
            f"Status Code: {response.status_code}, Response: {response.text}"
        )

    def post_text(self, text: str) -> Dict[str, Any]:
        """
        Creates a text-only post on the user's LinkedIn feed.
        """
        author_urn = self.get_my_profile_urn()
        
        url = f"{self.BASE_URL}/ugcPosts"
        payload = {
            "author": author_urn,
            "lifecycleState": "PUBLISHED",
            "specificContent": {
                "com.linkedin.ugc.ShareContent": {
                    "shareCommentary": {
                        "text": text
                    },
                    "shareMediaCategory": "NONE"
                }
            },
            "visibility": {
                "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
            }
        }

        logger.info("Sending text post to LinkedIn...")
        response = requests.post(url, headers=self.headers, json=payload)
        
        if response.status_code in [200, 201]:
            logger.info("LinkedIn post successfully published!")
            return response.json()
        else:
            raise Exception(f"Failed to post text to LinkedIn: {response.status_code} - {response.text}")

    def _register_image_upload(self, author_urn: str) -> tuple[str, str]:
        """
        Registers an upload request to get the upload URL and asset URN.
        Returns a tuple of (upload_url, asset_urn).
        """
        url = f"{self.BASE_URL}/assets?action=registerUpload"
        payload = {
            "registerUploadRequest": {
                "recipes": ["urn:li:digitalmediaRecipe:feedshare-image"],
                "owner": author_urn
            }
        }
        
        logger.info("Registering image upload with LinkedIn...")
        response = requests.post(url, headers=self.headers, json=payload)
        
        if response.status_code == 200:
            data = response.json()
            value = data["value"]
            upload_mech = value["uploadMechanism"]
            
            # Check both possible response structures for the upload URL
            if "com.linkedin.digitalmedia.uploading.MediaUploadHttpRequest" in upload_mech:
                upload_url = upload_mech["com.linkedin.digitalmedia.uploading.MediaUploadHttpRequest"]["uploadUrl"]
            elif "com.linkedin.digitalmedia.uploading.MediaUploadMechanism" in upload_mech:
                upload_url = upload_mech["com.linkedin.digitalmedia.uploading.MediaUploadMechanism"]["uploadUrl"]
            else:
                # Fallback to the first available key
                first_key = list(upload_mech.keys())[0]
                upload_url = upload_mech[first_key]["uploadUrl"]
                
            asset_urn = value["asset"]
            return upload_url, asset_urn
        else:
            raise Exception(f"Failed to register image upload: {response.status_code} - {response.text}")

    def _upload_image_binary(self, upload_url: str, image_path: str) -> None:
        """
        Uploads the raw binary image data to the registered LinkedIn upload URL.
        """
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Image not found at path: {image_path}")

        logger.info(f"Uploading image binary {image_path} to LinkedIn...")
        
        # Binary upload uses different headers
        upload_headers = {
            "Authorization": f"Bearer {self.access_token}"
        }
        
        # Read file as binary and PUT to upload_url
        with open(image_path, "rb") as image_file:
            response = requests.put(upload_url, headers=upload_headers, data=image_file)
            
        if response.status_code not in [200, 201]:
            raise Exception(f"Failed to upload image binary: {response.status_code} - {response.text}")
        logger.info("Image binary upload completed successfully.")

    def post_with_image(self, text: str, image_path: str, image_title: str = "Automated Post Visual") -> Dict[str, Any]:
        """
        Uploads an image first, then creates a post containing the text and the uploaded image.
        """
        author_urn = self.get_my_profile_urn()
        
        # Step 1: Register the image
        upload_url, asset_urn = self._register_image_upload(author_urn)
        
        # Step 2: Upload the binary image
        self._upload_image_binary(upload_url, image_path)
        
        # Step 3: Create the post referring to the uploaded image asset URN
        url = f"{self.BASE_URL}/ugcPosts"
        payload = {
            "author": author_urn,
            "lifecycleState": "PUBLISHED",
            "specificContent": {
                "com.linkedin.ugc.ShareContent": {
                    "shareCommentary": {
                        "text": text
                    },
                    "shareMediaCategory": "IMAGE",
                    "media": [
                        {
                            "status": "READY",
                            "description": {
                                "text": image_title
                            },
                            "media": asset_urn,
                            "title": {
                                "text": image_title
                            }
                        }
                    ]
                }
            },
            "visibility": {
                "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
            }
        }
        
        logger.info("Creating LinkedIn post with image attachment...")
        response = requests.post(url, headers=self.headers, json=payload)
        
        if response.status_code in [200, 201]:
            logger.info("LinkedIn image post successfully published!")
            return response.json()
        else:
            raise Exception(f"Failed to publish post with image: {response.status_code} - {response.text}")
