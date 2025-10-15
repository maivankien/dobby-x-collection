# Dobby X Collection Bot

A Discord bot that automatically collects and manages X (Twitter) links shared in Discord servers. The bot tracks links, users, and provides various commands to view and export collected data.

## Features

- **Automatic Link Detection**: Automatically detects and saves X/Twitter links from messages
- **User Tracking**: Tracks users who share links across different servers and channels
- **Statistics**: View total collected links count
- **User History**: View all links shared by a specific user
- **Latest Links**: Display the most recently shared links
- **Data Export**: Export all collected links to CSV format
- **Multi-Server Support**: Works across multiple Discord servers

## Commands

| Command | Description | Usage |
|---------|-------------|-------|
| `/collect` | Shows total number of collected X links | `/collect` |
| `/userlinks @user` | Displays all X links shared by a specific user | `/userlinks @username` |
| `/latest` | Shows the 5 most recently shared X links | `/latest` |
| `/export` | Exports all collected links to a CSV file | `/export` |

## Installation

### Prerequisites

- Python 3.8 or higher
- Discord Bot Token

### Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/maivankien/dobby-x-collection.git
   cd dobby-x-collection
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Create environment file**
   Create a `.env` file in the project root:
   ```env
   DISCORD_TOKEN=your_discord_bot_token_here
   ```

4. **Create data directory**
   ```bash
   mkdir data
   ```

5. **Run the bot**
   ```bash
   python main.py
   ```

## Bot Permissions

The bot requires the following Discord permissions:
- Read Messages
- Send Messages
- Read Message History
- Use Slash Commands

## Database Schema

The bot uses SQLite database with the following tables:

- **users**: Stores user information (ID, username, display name)
- **servers**: Stores Discord server information
- **channels**: Stores channel information linked to servers
- **x_links**: Stores collected X/Twitter links with metadata

## Configuration

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `DISCORD_TOKEN` | Discord bot token | Yes |

### Database

The database file is automatically created at `data/dobby_bot.db` on first run. The bot will initialize all required tables automatically.

## Usage Examples

### Viewing Statistics
```
/collect
```
Output: `📊 Total X links saved: 42`

### Checking User's Links
```
/userlinks @john_doe
```
Shows an embed with all X links shared by the mentioned user.

### Getting Latest Links
```
/latest
```
Displays the 5 most recently shared X links with user and channel information.

### Exporting Data
```
/export
```
Downloads a CSV file containing all collected links with metadata.

## Technical Details

- **Framework**: discord.py 2.6.3
- **Database**: SQLite with aiosqlite for async operations
- **Link Detection**: Uses regex pattern matching for X/Twitter URLs
- **File Format**: CSV export with UTF-8 encoding
