from . import db 
from typing import Dict
from bson import ObjectId
from datetime import datetime

# The database contains collections that store data and metadata about articles, their summaries, 
# along with the details of podcast episodes. 

class Episode():
    collection_name = "episodes"
# The collection 'episodes' stores the data of each episode and contains items with the following structure:
# {
#     "_id": ObjectId(),
#     "episode_name": "...",
#     "episode_num": ...,
#     "newsletter": "...",
#     "date": "Y/m/d",
#     "script": "...",
#     "status": "in production/script drafted" 
# }
    def __init__(self, episode_name: str, episode_num: int, newsletter: str='tldr newsletter',
                 _id: ObjectId=None, date: str=(datetime.now()).strftime('%Y/%m/%d'), script: str=None, status: str='in production'):
        self._id = _id if _id is not None else ObjectId()
        self.episode_name = episode_name
        self.episode_num = episode_num
        self.newsletter = newsletter
        self.date = date
        self.script = script
        self.status = status

    def to_dict(self) -> Dict:
        return {
            "_id": self._id,
            "episode_name": self.episode_name,
            "episode_num": self.episode_num,
            "newsletter": self.newsletter,
            "date": self.date,
            "script": self.script,
            "status": self.status
        }

    @classmethod
    def from_dict(cls, data: Dict):
        return cls(**data)
    
    @classmethod
    def from_mongo(cls, article_id: ObjectId):
        col = db[cls.collection_name]
        data = col.find_one({"_id", article_id})
        if not data:
            return None
        return cls(
            _id=data["_id"],
            episode_name=data["episode_name"],
            episode_num=data["episode_num"],
            newsletter=data.get("newsletter"),
            date=data.get("date"),
            script=data.get("script"),
            status=data.get("status"),
        )

    def save(self):
        '''
        Stores episode to the MongoDB database.
        '''
        try:
            articles_col = db["episodes"]
            doc = self.to_dict()
            # Try to insert first; if duplicate key error, update instead
            try:
                inserted_doc = articles_col.insert_one(doc)
                self._id = inserted_doc.inserted_id
            except:
                # Document already exists, update it
                articles_col.update_one({"_id": self._id}, {"$set": doc})
            return self._id
        except Exception as e:
            raise Exception(f'Could not save episode to database: {e}')
        
class Text():
    collection_name = "texts"
# The collection 'articles' stores the data of each article and contains items with the following structure:
# {
#     "_id": ObjectId(),
#     "episode_id": episode_id,
#     "url": "...",
#     "title": "...",
#     "newsletter": "tldr newsletter",
#     "full_text": "...",
#     "status": "not processed/text extracted"
# }
    def __init__(self, episode_id: ObjectId,
                 _id: ObjectId=None, newsletter: str = 'tldr newsletter', full_text: str=None, status: str='not processed'):
        self._id = _id if _id is not None else ObjectId()
        self.episode_id = episode_id
        self.newsletter = newsletter
        self.full_text = full_text
        self.status = status

    def to_dict(self) -> Dict:
        return {
            "_id": self._id,
            "episode_id": self.episode_id,
            "newsletter": self.newsletter,
            "full_text": self.full_text,
            "status": self.status
        }
    
    @classmethod
    def from_dict(cls, data: Dict):
        return cls(**data)
    
    @classmethod
    def from_mongo(cls, article_id: ObjectId):
        col = db[cls.collection_name]
        data = col.find_one({"_id", article_id})
        if not data:
            return None
        return cls(
            _id=data["_id"],
            episode_id=data["episode_id"],
            newsletter=data.get("newsletter"),
            full_text=data.get("full_text"),
            status=data.get("status"),
        )

    def save(self):
        '''
        Stores article to the MongoDB database.
        '''
        try:
            articles_col = db["texts"]
            doc = self.to_dict()
            try:
                inserted_doc = articles_col.insert_one(doc)
                self._id = inserted_doc.inserted_id
            except:
                # Document already exists, update it
                articles_col.update_one({"_id": self._id}, {"$set": doc})
            return self._id
        except Exception as e:
            raise Exception(f'Could not save text to database: {e}')
    
class Article():
    collection_name = "articles"
# The collection 'articles' stores the data of each article and contains items with the following structure:
# {
#     "_id": ObjectId(),
#     "episode_id": episode_id,
#     "url": "...",
#     "title": "...",
#     "newsletter": "tldr newsletter",
#     "full_text": "...",
#     "status": "not processed/text extracted"
# }
    def __init__(self, episode_id: ObjectId, url: str, 
                 _id: ObjectId=None, title: str=None, newsletter: str = 'tldr newsletter', full_text: str=None, status: str='not processed'):
        self._id = _id if _id is not None else ObjectId()
        self.episode_id = episode_id
        self.url = url
        self.title = title
        self.newsletter = newsletter
        self.full_text = full_text
        self.status = status

    def to_dict(self) -> Dict:
        return {
            "_id": self._id,
            "episode_id": self.episode_id,
            "url": self.url,
            "title": self.title,
            "newsletter": self.newsletter,
            "full_text": self.full_text,
            "status": self.status
        }
    
    @classmethod
    def from_dict(cls, data: Dict):
        return cls(**data)
    
    @classmethod
    def from_mongo(cls, article_id: ObjectId):
        col = db[cls.collection_name]
        data = col.find_one({"_id", article_id})
        if not data:
            return None
        return cls(
            _id=data["_id"],
            episode_id=data["episode_id"],
            url=data["url"],
            title=data.get("title"),
            newsletter=data.get("newsletter"),
            full_text=data.get("full_text"),
            status=data.get("status"),
        )

    def save(self):
        '''
        Stores article to the MongoDB database.
        '''
        try:
            articles_col = db["articles"]
            doc = self.to_dict()
            try:
                inserted_doc = articles_col.insert_one(doc)
                self._id = inserted_doc.inserted_id
            except:
                # Document already exists, update it
                articles_col.update_one({"_id": self._id}, {"$set": doc})
            return self._id
        except Exception as e:
            raise Exception(f'Could not save article to database: {e}')

class Chunk:
    collection_name="chunks"
# The collection 'chunks' stores the data of each chunk of an article for structured compression and contains items
# with the following structure:
# {
#     "_id": ObjectId(),
#     "article_id": article_id,
#     "chunk_text": "...",
#     "chunk_summary": "...",
#     "status": "not recombined/recombined"
# }
    def __init__(self, article_id: ObjectId, chunk_text: str, 
                 _id: ObjectId=None, chunk_summary: str=None, status: str='not recombined'):
        self._id = _id if _id is not None else ObjectId()
        self.article_id = article_id
        self.chunk_text = chunk_text
        self.chunk_summary= chunk_summary
        self.status = status

    def to_dict(self):
        return {
            "_id": self._id,
            "article_id": self.article_id,
            "chunk_text": self.chunk_text,
            "chunk_summary": self.chunk_summary,
            "status": self.status
        }
    
    @classmethod
    def from_dict(cls, data: Dict):
        return cls(**data)
    
    @classmethod
    def from_mongo(cls, article_id: ObjectId):
        col = db[cls.collection_name]
        data = col.find_one({"_id": article_id})
        if not data:
            return None
        return cls(
            _id=data["_id"],
            article_id = data["article_id"],
            chunk_text = data["chunk_text"],
            chunk_summary = data.get("chunk_summary"),
            status = data.get("status")
        )
    
    def save(self):
        '''
        Stores chunk to MongoDB database.
        '''
        try:
            chunks_col = db["chunks"]
            doc = self.to_dict()
            try:
                inserted_doc = chunks_col.insert_one(doc)
                self._id = inserted_doc.inserted_id
            except:
                # Document already exists, update it
                chunks_col.update_one({"_id": self._id}, {"$set": doc})
            return self._id
        except Exception as e:
            raise Exception(f'Could not save chunk to database: {e}')
        
class Summary:
    collection_name = "summaries"
# The collection 'summaries' stores the summaries of each article, which is the result of combining the compressed chunks. 
# Items have the following structure:
# {
#     "_id": ObjectId(),
#     "article_id": article_id,
#     "summary": "...",
# }
    def __init__(self, article_id: ObjectId, _id: ObjectId=None, summary_text: str=None):
        self._id = _id if _id is not None else ObjectId()
        self.article_id = article_id
        self.summary_text = summary_text

    def to_dict(self):
        return {
            "_id": self._id,
            "article_id": self.article_id,
            "summary_text": self.summary_text
        }
    
    @classmethod
    def from_dict(cls, data: Dict):
        return cls(**data)
    
    @classmethod
    def from_mongo(cls, article_id: ObjectId):
        col = db[cls.collection_name]
        data = col.find_one({"_id": article_id})
        if not data:
            return None
        return cls(
            _id = data["_id"],
            article_id = data["article_id"],
            summary_text = data["summary_text"]
        )
    
    def save(self):
        '''
        Saves summary to 'summaries' collection in database.
        '''
        try:
            summaries_col = db["summaries"]
            doc = self.to_dict()
            try:
                inserted_doc = summaries_col.insert_one(doc)
                self._id = inserted_doc.inserted_id
            except:
                # Document already exists, update it
                summaries_col.update_one({"_id": self._id}, {"$set": doc})
            return self._id
        except Exception as e:
            raise Exception(f'Could not save summary to database: {e}')


    

            

        