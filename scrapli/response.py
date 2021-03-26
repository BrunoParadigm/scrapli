"""scrapli.response"""
from collections import UserList
from datetime import datetime
from io import TextIOWrapper
from typing import (
    Any,
    Dict,
    List,
    Optional,
    TYPE_CHECKING,
    Union,
)

from scrapli.exceptions import ScrapliCommandFailure
from scrapli.helper import (
    _textfsm_get_template,
    genie_parse,
    textfsm_parse,
    ttp_parse,
)


class Response:
    def __init__(
            self,
            host: str,
            channel_input: str,
            initial_prompt: str,
            textfsm_platform: str = "",
            genie_platform: str = "",
            failed_when_contains: Optional[Union[str, List[str]]] = None,
    ):
        """
        Scrapli Response

        Store channel_input, resulting output, and start/end/elapsed time information. Attempt to
        determine if command was successful or not and reflect that in a failed attribute.

        Args:
            host: host that was operated on
            initial_prompt: shows the initial prompt before the input was sent
            channel_input: input that got sent down the channel
            textfsm_platform: ntc-templates friendly platform type
            genie_platform: cisco pyats/genie friendly platform type
            failed_when_contains: list of strings that, if present in final output, represent a
                failed command/interaction

        Returns:
            None

        Raises:
            N/A

        """
        self.host = host
        self.initial_prompt = initial_prompt
        self.response_prompt: Optional[str] = None
        self.prompt_change: bool = False
        self.start_time = datetime.now()
        self.finish_time: Optional[datetime] = None
        self.elapsed_time: Optional[float] = None

        self.channel_input = channel_input
        self.textfsm_platform = textfsm_platform
        self.genie_platform = genie_platform
        self.raw_result: bytes = b""
        self.result: str = ""

        if isinstance(failed_when_contains, str):
            failed_when_contains = [failed_when_contains]
        self.failed_when_contains = failed_when_contains
        self.failed = True

    def __bool__(self) -> bool:
        """
        Magic bool method based on channel_input being failed or not

        Args:
            N/A

        Returns:
            bool: True/False if channel_input failed

        Raises:
            N/A

        """
        return self.failed

    def __repr__(self) -> str:
        """
        Magic repr method for Response class

        Args:
            N/A

        Returns:
            str: repr for class object

        Raises:
            N/A

        """
        return f"Response <Success: {str(not self.failed)}>"

    def __str__(self) -> str:
        """
        Magic str method for Response class

        Args:
            N/A

        Returns:
            str: str for class object

        Raises:
            N/A

        """
        return f"Response <Success: {str(not self.failed)}>"

    def console_output(self) -> str:
        """Display's what the console output would have looked like.

        An exmaple of console output would be:

        '''
        cisco-ios-device# show run | inc booted
        boot system switch all flash:cat9k_iosxe.16.10.01.SPA.conf
        license boot level network-advantage addon dna-advantage
        '''

        diagnostic bootup level minimal
        Args:
            N/A

        Returns:
            string of what the original prompt, input, and outputu would have
            looked like in the console.

        Raises:
            N/A

        """
        console_output = f"{self.initial_prompt}{self.channel_input}\n"

        if self.result:
            console_output += f"{self.result}\n"

        return console_output

    def record_response(self, result: bytes) -> None:
        """
        Record channel_input results and elapsed time of channel input/reading output

        Args:
            result: string result of channel_input

        Returns:
            None

        Raises:
            N/A

        """
        self.finish_time = datetime.now()
        self.elapsed_time = (
                self.finish_time - self.start_time).total_seconds()
        self.raw_result = result
        self.result = result.decode()
        if not self.failed_when_contains:
            self.failed = False
        elif not any(err in self.result for err in self.failed_when_contains):
            self.failed = False

    def textfsm_parse_output(self, to_dict: bool = True) -> Union[
        Dict[str, Any], List[Any]]:
        """
        Parse results with textfsm, always return structured data

        Returns an empty list if parsing fails!

        Args:
            to_dict: convert textfsm output from list of lists to list of dicts -- basically create
                dict from header and row data so it is easier to read/parse the output

        Returns:
            structured_result: empty list or parsed data from textfsm

        Raises:
            N/A

        """
        template = _textfsm_get_template(platform=self.textfsm_platform,
                                         command=self.channel_input)
        if isinstance(template, TextIOWrapper):
            structured_result = (
                    textfsm_parse(template=template, output=self.result,
                                  to_dict=to_dict) or []
            )
        else:
            structured_result = []
        return structured_result

    def genie_parse_output(self) -> Union[Dict[str, Any], List[Any]]:
        """
        Parse results with genie, always return structured data

        Returns an empty list if parsing fails!

        Args:
            N/A

        Returns:
            structured_result: empty list or parsed data from genie

        Raises:
            N/A

        """
        structured_result = genie_parse(
                platform=self.genie_platform, command=self.channel_input,
                output=self.result
        )
        return structured_result

    def ttp_parse_output(
            self, template: Union[str, TextIOWrapper]
    ) -> Union[Dict[str, Any], List[Any]]:
        """
        Parse results with ttp, always return structured data

        Returns an empty list if parsing fails!

        Args:
            template: string path to ttp template or opened ttp template file

        Returns:
            structured_result: empty list or parsed data from ttp

        Raises:
            N/A

        """
        structured_result = ttp_parse(template=template,
                                      output=self.result) or []
        return structured_result

    def raise_for_status(self) -> None:
        """
        Raise a `ScrapliCommandFailure` if command/config failed

        Args:
            N/A

        Returns:
            None

        Raises:
            ScrapliCommandFailure: if command/config failed

        """
        if self.failed:
            raise ScrapliCommandFailure()


class ConfigResponse(Response):
    """Response from a configuration command"""

    def __repr__(self) -> str:
        """
        Magic repr method for Response class

        Args:
            N/A

        Returns:
            str: repr for class object

        Raises:
            N/A

        """
        return f"ConfigCommandResponse <Success: {str(not self.failed)}>"

    def __str__(self) -> str:
        """
        Magic str method for Response class

        Args:
            N/A

        Returns:
            str: str for class object

        Raises:
            N/A

        """
        return f"ConfigCommandResponse <Success: {str(not self.failed)}>"

    def console_output(self) -> str:
        """Display's what the console output would have looked like for a
        configuration command.

        Args:
            N/A

        Returns:
            string of what the original prompt, input, and output would have
            looked like in the console.

        Raises:
            N/A

        """
        console_output = f"{self.initial_prompt}{self.channel_input}\n"
        if self.result and self.response_prompt:
            console_output += f"{self.result}\n"

        return console_output


if TYPE_CHECKING:
    ScrapliMultiResponse = UserList[
        Response, ConfigResponse]  # pylint:  disable=E1136; # pragma:  no cover
else:
    ScrapliMultiResponse = UserList


class MultiResponse(ScrapliMultiResponse):
    def __repr__(self) -> str:
        """
        Magic repr method for MultiResponse class

        Args:
            N/A

        Returns:
            str: repr for class object

        Raises:
            N/A

        """
        return (
            f"MultiResponse <Success: {str(not self.failed)}; "
            f"Response Elements: {len(self.data)}>"
        )

    def __str__(self) -> str:
        """
        Magic str method for MultiResponse class

        Args:
            N/A

        Returns:
            str: str for class object

        Raises:
            N/A

        """
        return (
            f"MultiResponse <Success: {str(not self.failed)}; "
            f"Response Elements: {len(self.data)}>"
        )

    @property
    def failed(self) -> bool:
        """
        Determine if any elements of MultiResponse are failed

        Args:
            N/A

        Returns:
            bool: True for failed

        Raises:
            N/A

        """
        if any(response.failed for response in self.data):
            return True
        return False

    @property
    def result(self) -> str:
        """
        Build a unified result from all elements of MultiResponse

        Args:
            N/A

        Returns:
            str: Unified result by combining results of all elements of MultiResponse

        Raises:
            N/A

        """
        result = ""
        for response in self.data:
            result += "\n".join([response.channel_input, response.result])
        return result

    @property
    def console_output(self) -> str:
        """
        Build a unified console output from all elements of MultiResponse

        This is used to display what the original input and output would have
        looked like in the console cli.

        Args:
            N/A

        Returns:
            str: Unified result by combining results of all elements of MultiResponse

        Raises:
            N/A
        """
        result = ""

        for response in self.data:
            result += "\n".join([response.console_output()])
        return result

    def raise_for_status(self) -> None:
        """
        Raise a `ScrapliCommandFailure` if any elements are failed

        Args:
            N/A

        Returns:
            None

        Raises:
            ScrapliCommandFailure: if any elements are failed

        """
        if self.failed:
            raise ScrapliCommandFailure()
