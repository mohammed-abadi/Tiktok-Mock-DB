## 🗄️ Database Schema (ERD)

The TikTok Hub backend is built on a relational PostgreSQL database. The architecture is designed to handle a complex social graph, allowing for real-time messaging, asymmetrical following, and multi-threaded commenting.

### 1. Entity Relationship Diagram
The following diagram illustrates the interconnected nature of the Hub ecosystem:

![TikTok Hub ERD](./Images/Untitled%20Diagram.png)

### 2. Relationship Architecture

* **The Social Core:** A 1:1 link between **User** and **Profile** handles identity, while the **Followers** table manages the many-to-many social graph.
* **Content & Engagement:** **Posts** (supporting Reels via boolean) are linked to **Likes**, **Favorites**, and **Reposts**. 
* **Conversational Engine:** A complex relationship between **Participants**, **Conversations**, and **Messages** allows for secure, multi-user direct messaging.
* **Deep Interaction:** The **Comment** model supports nested interactions via a self-referencing `parent_comment_id`, enabling organized discussion threads.
* **Discovery:** A many-to-many join via **Post_Topic** ensures posts are discoverable through the **Topic** system.

### 3. Logic Implementation
* **The "Reels" Engine:** Posts are flagged with `is_reel`. The API filters these for the vertical-scroll feed while tracking `view_count` for analytics.
* **Messaging Flow:** Messages are tied to a `Conversation` rather than just two users, allowing the schema to scale to group chats easily.
* **Threaded Comments:** By using a foreign key to itself on the Comment model, we can render "replies to replies" just like on Instagram or TikTok.
