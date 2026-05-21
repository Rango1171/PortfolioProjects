/*
  # Create Annotation Sessions Table

  1. New Tables
    - `annotation_sessions`
      - `id` (uuid, primary key) - Unique session identifier
      - `user_id` (uuid, optional) - Future user authentication
      - `image_name` (text) - Original image filename
      - `image_data` (text) - Base64-encoded image data
      - `boxes_data` (text) - JSON string containing all bounding boxes
      - `created_at` (timestamptz) - Session creation timestamp
      - `updated_at` (timestamptz) - Last update timestamp

  2. Security
    - Enable RLS on `annotation_sessions` table
    - All data is treated as public for now (no user-specific restrictions)
    - RLS policies prevent unauthorized access in future versions
*/

CREATE TABLE IF NOT EXISTS annotation_sessions (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id uuid,
  image_name text NOT NULL,
  image_data text,
  boxes_data text NOT NULL DEFAULT '[]',
  created_at timestamptz DEFAULT now(),
  updated_at timestamptz DEFAULT now()
);

ALTER TABLE annotation_sessions ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Allow public read access"
  ON annotation_sessions
  FOR SELECT
  TO public
  USING (true);

CREATE POLICY "Allow public insert"
  ON annotation_sessions
  FOR INSERT
  TO public
  WITH CHECK (true);

CREATE POLICY "Allow public update"
  ON annotation_sessions
  FOR UPDATE
  TO public
  USING (true)
  WITH CHECK (true);

CREATE POLICY "Allow public delete"
  ON annotation_sessions
  FOR DELETE
  TO public
  USING (true);
