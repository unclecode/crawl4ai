from functools import cached_property
from typing import Annotated, Any, Literal, Self, Union

from crawl4ai.extraction_strategy import DEFAULT_PROVIDER
from pydantic import BaseModel, ConfigDict, Field, TypeAdapter


class LLMExtraction(BaseModel):
    extraction_strategy: Literal["llm"]
    provider: Annotated[str, Field(alias="llmProvider")] = DEFAULT_PROVIDER
    api_token: Annotated[str | None, Field(alias="llmApiToken")] = None
    instruction: Annotated[str | None, Field(alias="llmInstruction")] = None


class JsonCssExtractionSchemaField(BaseModel):
    name: Annotated[str, Field()]
    selector: Annotated[str, Field()]
    type: Annotated[str, Field()]
    attribute: Annotated[str | None, Field()] = None
    fields: Annotated[list[Self] | None, Field()] = None


class JsonCssExtractionSchema(BaseModel):
    name: Annotated[str, Field()]
    base_selector: Annotated[str, Field(alias="baseSelector")]
    fields: Annotated[list[JsonCssExtractionSchemaField], Field()]


class JsonCssExtraction(BaseModel):
    extraction_strategy: Literal["jsonCss"]
    extraction_schema: Annotated[dict[str, Any], Field(alias="jsonCssSchema")]


class CosineExtraction(BaseModel):
    extraction_strategy: Literal["cosine"]
    semantic_filter: Annotated[str | None, Field(alias="cosineSemanticFilter")]
    word_count_threshold: Annotated[int, Field(alias="cosineWordCountThreshold")] = 20
    max_dist: Annotated[float, Field(alias="cosineMaxDist")] = 0.2
    linkage_method: Annotated[str, Field(alias="cosineLinkageMethod")] = "ward"
    top_k: Annotated[int, Field(alias="cosineTopK")] = 3
    extraction_model_name: Annotated[str, Field(alias="cosineModelName")] = (
        "sentence-transformers/all-MiniLM-L6-v2"
    )
    sim_threshold: Annotated[float, Field(alias="cosineSimThreshold")] = 0.3


class Input(BaseModel):
    model_config = ConfigDict(extra="allow")

    start_urls: Annotated[list[Any], Field(alias="startUrls", min_length=1)]
    proxy_configuration: Annotated[
        dict[str, Any] | None, Field(alias="proxyConfiguration")
    ] = None
    magic_mode: Annotated[bool, Field(alias="magicMode")] = True
    save_screenshots: Annotated[bool, Field(alias="saveScreenshots")] = False
    css_selector: Annotated[str | None, Field(alias="cssSelector")] = None
    wait_for: Annotated[str | None, Field(alias="waitFor")] = None
    js_code: Annotated[str | None, Field(alias="jsCode")] = None

    extraction_strategy_: Annotated[str | None, Field(alias="extractionStrategy")] = (
        None
    )

    @cached_property
    def extraction_strategy(
        self,
    ) -> Union[CosineExtraction, LLMExtraction, JsonCssExtraction, None]:
        if not self.__pydantic_extra__ or self.extraction_strategy_ is None:
            return None

        adapter = TypeAdapter(
            Annotated[
                Union[CosineExtraction, LLMExtraction, JsonCssExtraction],
                Field(discriminator="extraction_strategy"),
            ]
        )

        return adapter.validate_python(
            {
                **self.__pydantic_extra__,
                "extraction_strategy": self.extraction_strategy_,
            }
        )
