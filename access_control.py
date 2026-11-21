"""
Hides user credentials, manages sessions, and controls role permissions.
"""

import hashlib, hmac, secrets
# hashlib converts passwords into hashes using PBKDF2
# hmac compares passwords during login
# secrets makes random values like salts and session tokens 

from .models import Result

class AccessControl:
    def __init__(self):
        self.__users = {}
        self.__sessions = {}

        self.__permissions = {
            "nurse": 
            ["dashboard:view", "alarms:view", "alarms:acknowledge"],

            "pharmacist":
            ["dashboard:view", "alarms:view", "alarms:acknowledge", 
             "inventory:view", "history:view"],

            "technician":
            ["dashboard:view", "alarms:view", "health:view", "history:view"],

            "administrator":
            ["dashboard:view", "alarms:view", "alarms:acknowledge",
             "inventory:view", "health:view", "history:view", "reports:view"]
        }


    def add_user(self, username, password, role):
        if not isinstance(username, str) or not username.strip():
            return Result(False, "Invalid username")

        if username in self.__users:
            return Result(False, "Username is taken")

        if not isinstance(password, str) or not password:
            return Result(False, "Invalid password")

        if role not in self.__permissions:
            return Result(False, "Invalid role")

        try: 
            salt = secrets.token_bytes(16)
            # generates 16 random bytes

            password_hash = hashlib.pbkdf2_hmac(
                "sha256", password.encode(), salt, 150000)
            # sha256 is the hashing algorithm used inside pbkdf2
            # password.encode() turns password from string into bytes 
            # random salt we generated earlier - this is to make the hash 
            #    unique even if two passwords are the same
            # 150k is the number of hashing iterations which makes protects passwords more

        except (ValueError, UnicodeError) as error:
            # unicode error comes up when encoding text errors
            return Result(False, "Could not process password: " + str(error))

        self.__users[username] = {
            "salt": salt, "password_hash": password_hash, "role": role}

        return Result(True, "User created")


    def login(self, username, password):
        if not isinstance(username, str) or not isinstance(password, str):
            return Result(False, "Invalid credentials")

        user = self.__users.get(username)

        if user is None:
            return Result(False, "Invalid credentials")

        try: 
            entered_hash = hashlib.pbkdf2_hmac("sha256", password.encode(), user["salt"], 150000)

        except (ValueError, UnicodeError):
            return Result(False, "Invalid credentials")

        if not hmac.compare_digest(entered_hash, user["password_hash"]):
        # comparing the hash generated for the entered password with the users original password hash
            return Result(False, "Invalid credentials")

        token = secrets.token_urlsafe(24)
        # urlsafe comes up with a random 24 byte str to use as a token
        # this will be different each time of course and acts as a temporary access key

        self.__sessions[token] = username  # associating token to user so they don't have to put in password again

        return Result(True, "Login successful", {"token": token})


    def authorize(self, token, permission):
        # invalid or missing session cant grant access
        if not isinstance(token, str):
            return False

        username = self.__sessions.get(token)
        # token indentifies who is logged in
        # username finds which user owns that token

        if username is None:
        # if no token was found
            return False

        role = self.__users[username]["role"]
        # find users role

        return permission in self.__permissions[role]
        # returns True if the token is valid and their role has permission


    def get_username(self, token):
        if not isinstance(token, str):
            return None

        return self.__sessions.get(token)
        # finding the user that owns that token


    def logout(self, token):
        if not isinstance(token, str) or token not in self.__sessions:
            return Result(False, "Invalid session")

        del self.__sessions[token]

        return Result(True, "Logged out")
    