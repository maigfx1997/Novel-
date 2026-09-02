import {
  pgTable,
  serial,
  text,
  integer,
  timestamp,
  jsonb,
} from "drizzle-orm/pg-core";

export const novels = pgTable("novels", {
  id: serial("id").primaryKey(),
  title: text("title").notNull(),
  author: text("author").notNull().default(""),
  description: text("description").notNull().default(""),
  coverUrl: text("cover_url").notNull().default(""),
  sourceUrl: text("source_url").notNull(),
  sourceType: text("source_type").notNull(), // 'wattpad' | 'novlar' | 'uranus'
  totalChapters: integer("total_chapters").notNull().default(0),
  chapters: jsonb("chapters").notNull().default([]),
  createdAt: timestamp("created_at").defaultNow().notNull(),
  updatedAt: timestamp("updated_at").defaultNow().notNull(),
});

export type Novel = typeof novels.$inferSelect;
export type NewNovel = typeof novels.$inferInsert;
