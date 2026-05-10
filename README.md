## 🗄️ Database Schema (ERD)

The TikTok Hub backend is built on a relational PostgreSQL database. The architecture is designed to handle a complex social graph, allowing for asymmetrical following, content reposting, and multi-layered engagement (likes/favorites).

### 1. Entity Relationship Diagram
The following relationships define the social ecosystem:

* **User ↔ Profile (1:1):** Every authenticated user has a unique social identity.
* **Profile ↔ Profile (M:N Self):** Asymmetrical following system (Followers/Following).
* **User ↔ Post (1:N):** One-to-many relationship defining authorship.
* **Post ↔ Post (1:N Self):** Recursive relationship to track "Repost" or "Duet" lineage.
* **User ↔ Post (M:N):** High-performance join tables for Likes and Favorites.
* **Post ↔ Topic (M:N):** Categorization system for "Discover" feed filtering.



### 2. Data Models Breakdown

| Entity | Primary Role | Key Fields |
| :--- | :--- | :--- |
| **User** | Authentication | Username, Email, Password |
| **Profile** | Social Identity | Bio, Avatar, Following (M:N) |
| **Post** | Content Hub | IsReel (Bool), Caption, MediaURL, RepostOf (FK) |
| **Topic** | Discovery | Name (Unique) |

### 3. Logic Implementation
* **The "Reels" Engine:** Posts are flagged with a boolean `is_reel`. The API filters these for the vertical-scroll feed.
* **Liked Videos Tab:** Leveraging the `related_name='liked_posts'` on the Post model, we can retrieve a user's entire liked gallery with a single query: `request.user.liked_posts.filter(is_reel=True)`.
* **Social Graph:** Using `symmetrical=False` on the Profile Many-to-Many field allows for a "TikTok-style" follow system where follow-backs are not mandatory.
