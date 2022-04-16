import uuid
from abc import abstractmethod
from copy import deepcopy
from typing import Any, Dict, List, Optional, Union
from uuid import uuid4

import mmh3
import numpy as np


class Document:
    def __init__(
        self,
        text: str,
        id: Optional[str] = None,
        score: Optional[float] = None,
        probability: Optional[float] = None,
        question: Optional[str] = None,
        meta: Dict[str, Any] = None,
        embedding: Optional[np.ndarray] = None,
        id_hash_keys: Optional[List[str]] = None,
        uuid_type: Optional[str] = None,
    ):
        """

        Note: There can be multiple Documents originating from one file (e.g. PDF), if you split the text
        into smaller passages. We'll have one Document per passage in this case.

        Each document has a unique ID. This can be supplied by the user or generated automatically.
        It's particularly helpful for handling of duplicates and referencing documents in other objects (e.g. Labels)

        There's an easy option to convert from/to dicts via `from_dict()` and `to_dict`.

        :param text: Text of the document
        :param id: Unique ID for the document. If not supplied by the user, we'll generate one automatically by
                   creating a hash from the supplied text. This behaviour can be further adjusted by `id_hash_keys`.
        :param score: Retriever's query score for a retrieved document
        :param probability: a pseudo probability by scaling score in the range 0 to 1
        :param question: Question text (e.g. for FAQs where one document usually consists of one question and one answer text).
        :param meta: Meta fields for a document like name, url, or author.
        :param embedding: Vector encoding of the text
        :param id_hash_keys: Generate the document id from a custom list of strings.
                             If you want ensure you don't have duplicate documents in your DocumentStore but texts are
                             not unique, you can provide custom strings here that will be used (e.g. ["filename_xy", "text_of_doc"].
        """

        self.text = text
        self.score = score
        self.probability = probability
        self.question = question
        self.meta = meta or {}
        self.embedding = embedding

        self.id = self._get_id(id_hash_keys, uuid_type=uuid_type) if id is None else str(id)

    def _get_id(self, id_hash_keys, uuid_type=None):
        if uuid_type is None:
            return "{:02x}".format(mmh3.hash128(self.text, signed=False))
        elif uuid_type == "uuid3":
            return str(uuid.uuid3(uuid.NAMESPACE_DNS, self.text))
        elif uuid_type == 'uuid5':
            return str(uuid.uuid5(uuid.NAMESPACE_DNS, self.text))
        else:
            raise ValueError(f"Choose either \"uuid3\" or \"uuid5\" or None")

    def to_dict(self, field_map={}):
        inv_field_map = {v: k for k, v in field_map.items()}
        _doc: Dict[str, str] = {}
        for k, v in self.__dict__.items():
            k = k if k not in inv_field_map else inv_field_map[k]
            _doc[k] = v
        return _doc

    @classmethod
    def from_dict(cls, dict, field_map={}, uuid_type=None):
        _doc = deepcopy(dict)
        init_args = [
            "text",
            "id",
            "score",
            "probability",
            "question",
            "meta",
            "embedding",
        ]
        if "meta" not in _doc.keys():
            _doc["meta"] = {}
        # copy additional fields into "meta"
        for k, v in _doc.items():
            if k not in init_args and k not in field_map:
                _doc["meta"][k] = v
        # remove additional fields from top level
        _new_doc = {}
        for k, v in _doc.items():
            if k in init_args:
                _new_doc[k] = v
            elif k in field_map:
                k = field_map[k]
                _new_doc[k] = v

        if uuid_type:
            _new_doc["uuid_type"] = uuid_type

        return cls(**_new_doc)

    def __repr__(self):
        return str(self.to_dict())


class Label:
    def __init__(
        self,
        question: str,
        answer: str,
        is_correct_answer: bool,
        is_correct_document: bool,
        origin: str,
        id: Optional[str] = None,
        document_id: Optional[str] = None,
        offset_start_in_doc: Optional[int] = None,
        no_answer: Optional[bool] = None,
        model_id: Optional[int] = None,
        created_at: Optional[str] = None,
        updated_at: Optional[str] = None,
    ):
        """

        :param question: the question(or query) for finding answers.
        :param answer: the answer string.
        :param is_correct_answer: whether the sample is positive or negative.
        :param is_correct_document: in case of negative sample(is_correct_answer is False), there could be two cases;
                                    incorrect answer but correct document & incorrect document. This flag denotes if
                                    the returned document was correct.
        :param origin: the source for the labels. It can be used to later for filtering.
        :param id: Unique ID used within the DocumentStore. If not supplied, a uuid will be generated automatically.
        :param document_id: the document_store's ID for the returned answer document.
        :param offset_start_in_doc: the answer start offset in the document.
        :param no_answer: whether the question in unanswerable.
        :param model_id: model_id used for prediction (in-case of user feedback).
        :param created_at: Timestamp of creation with format yyyy-MM-dd HH:mm:ss.
                           Generate in Python via time.strftime("%Y-%m-%d %H:%M:%S").
        :param created_at: Timestamp of update with format yyyy-MM-dd HH:mm:ss.
                           Generate in Python via time.strftime("%Y-%m-%d %H:%M:%S")
        """

        # Create a unique ID (either new one, or one from user input)
        if id:
            self.id = str(id)
        else:
            self.id = str(uuid4())

        self.created_at = created_at
        self.updated_at = updated_at
        self.question = question
        self.answer = answer
        self.is_correct_answer = is_correct_answer
        self.is_correct_document = is_correct_document
        self.origin = origin
        self.document_id = document_id
        self.offset_start_in_doc = offset_start_in_doc
        self.no_answer = no_answer
        self.model_id = model_id

    @classmethod
    def from_dict(cls, dict):
        return cls(**dict)

    def to_dict(self):
        return self.__dict__

    # define __eq__ and __hash__ functions to deduplicate Label Objects
    def __eq__(self, other):
        return (
            isinstance(other, self.__class__)
            and getattr(other, 'question', None) == self.question
            and getattr(other, 'answer', None) == self.answer
            and getattr(other, 'is_correct_answer', None) == self.is_correct_answer
            and getattr(other, 'is_correct_document', None) == self.is_correct_document
            and getattr(other, 'origin', None) == self.origin
            and getattr(other, 'document_id', None) == self.document_id
            and getattr(other, 'offset_start_in_doc', None) == self.offset_start_in_doc
            and getattr(other, 'no_answer', None) == self.no_answer
            and getattr(other, 'model_id', None) == self.model_id
            and getattr(other, 'created_at', None) == self.created_at
            and getattr(other, 'updated_at', None) == self.updated_at
        )

    def __hash__(self):
        return hash(
            self.question
            + self.answer
            + str(self.is_correct_answer)
            + str(self.is_correct_document)
            + str(self.origin)
            + str(self.document_id)
            + str(self.offset_start_in_doc)
            + str(self.no_answer)
            + str(self.model_id)
        )

    def __repr__(self):
        return str(self.to_dict())

    def __str__(self):
        return str(self.to_dict())


class BaseDocStore:
    """
    Base class for implementing Document Stores.
    """

    index: Optional[str]
    label_index: Optional[str]
    similarity: Optional[str]

    @abstractmethod
    def write_documents(
        self,
        documents: Union[List[dict], List[Document]],
        index: Optional[str] = None,
        batch_size: int = 10_000,
    ):
        """
        Indexes documents for later queries.

        :param documents: a list of Python dictionaries or a list of Haystack Document objects.
                          For documents as dictionaries, the format is {"text": "<the-actual-text>"}.
                          Optionally: Include meta data via {"text": "<the-actual-text>",
                          "meta":{"name": "<some-document-name>, "author": "somebody", ...}}
                          It can be used for filtering and is accessible in the responses of the Finder.
        :param index: Optional name of index where the documents shall be written to.
                      If None, the DocumentStore's default index (self.index) will be used.
        :param batch_size: Number of documents that are passed to bulk function at a time.

        :return: None
        """
        pass

    @abstractmethod
    def get_all_documents(
        self,
        index: Optional[str] = None,
        filters: Optional[Dict[str, List[str]]] = None,
        return_embedding: Optional[bool] = None,
    ) -> List[Document]:
        """
        Get documents from the document store.

        :param index: Name of the index to get the documents from. If None, the
                      DocumentStore's default index (self.index) will be used.
        :param filters: Optional filters to narrow down the documents to return.
                        Example: {"name": ["some", "more"], "category": ["only_one"]}
        :param return_embedding: Whether to return the document embeddings.
        """
        pass

    @abstractmethod
    def get_document_count(
        self,
        filters: Optional[Dict[str, List[str]]] = None,
        index: Optional[str] = None,
    ) -> int:
        pass

    @abstractmethod
    def query_by_embedding(
        self,
        query_emb: np.ndarray,
        filters: Optional[Optional[Dict[str, List[str]]]] = None,
        top_k: int = 10,
        index: Optional[str] = None,
        return_embedding: Optional[bool] = None,
    ) -> List[Document]:
        pass

    @abstractmethod
    def delete_documents(
        self,
        index: Optional[str] = None,
        filters: Optional[Dict[str, List[str]]] = None,
    ):
        pass

    @abstractmethod
    def get_documents_by_id(self, ids: List[str], index: Optional[str] = None, batch_size: int = 10_000) -> List[Document]:
        pass

    def _handle_duplicate_documents(
        self, documents: List[Document], index: Optional[str] = None, duplicate_documents: Optional[str] = None
    ):
        """
        Checks whether any of the passed documents is already existing in the chosen index and returns a list of
        documents that are not in the index yet.

        :param documents: A list of Haystack Document objects.
        :param duplicate_documents: Handle duplicates document based on parameter options.
                                    Parameter options : ( 'skip','overwrite','fail')
                                    skip (default option): Ignore the duplicates documents
                                    overwrite: Update any existing documents with the same ID when adding documents.
                                    fail: an error is raised if the document ID of the document being added already
                                    exists.
        :return: A list of Haystack Document objects.
        """

        index = index or self.index
        if duplicate_documents in ('skip', 'fail'):
            documents = self._drop_duplicate_documents(documents)
            documents_found = self.get_documents_by_id(ids=[doc.id for doc in documents], index=index)
            ids_exist_in_db: List[str] = [doc.id for doc in documents_found]

            if len(ids_exist_in_db) > 0 and duplicate_documents == 'fail':
                raise DuplicateDocumentError(
                    f"Document with ids '{', '.join(ids_exist_in_db)} already exists" f" in index = '{index}'."
                )

            documents = list(filter(lambda doc: doc.id not in ids_exist_in_db, documents))

        return documents
