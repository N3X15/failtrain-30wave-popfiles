import collections

class KeyValues(collections.MutableMapping):
    """Class for representing Key Values objects, with container behavior.

    This class implements the tree data structure used by KeyValues, exposing
    method for acting like a python Dictionary, but keeping the key order.

    It also implements methods for representing its data as a string.
    """

    def __init__(self, name=""):
        self._parent = None
        self._children = collections.OrderedDict()

        self._name = name

    # Container interface
    def __contains__(self, key):
        return key in self._children

    # Iterable interface
    def __iter__(self):
        return iter(self._children)

    # Sized interface
    def __len__(self):
        return len(self._children)

    # Mapping interface
    def __getitem__(self, key):
        return self._children[key]

    # MutableMapping interface
    def __setitem__(self, key, value):
        if isinstance(value, KeyValues):
            value._parent = self
        self._children[key] = value

    def __delitem__(self, key):
        del self._children[key]

    # String conversion
    def __str__(self):
        return self.stringify()
        
    def get_indent_for_keys(self,d):
        """ 
        Returns the minimum number of spaces that keys should be padded with for this block.
        
        Used to align keys during stringification.
        """
        max_indent=0
        for key in d:
            kl = len(key)
            if kl>max_indent:
                max_indent=kl
        return max_indent+1
        
    def stringify(self, indentation=True, inline=False, space="\t"):
        """Returns the data as a string, with optional formating.

        The method generates a multiline indented string, in a similar format to
        that found on files. It's also able to create inline representation of
        the Key Value, without line breaks.

        Keyword arguments:
        indentation -- If the result should be indented (default True)
        inline -- If the string should be returned without line breaks. Setting
        this True will override indentation to False (default False)
        space -- String used to indentation (default "\t")
        """

        line_break = "\n"
        if inline:
            indentation = False
            line_break = " "

        if not indentation:
            space = ""

        result = self._escape(str(self._name)) + line_break
        result += self._stringify_recursive(indentation, line_break, space, 0)

        return result

    def _stringify_recursive(self, indentation, line_break, space, indentation_level):
        prefix = space * indentation_level
        prefix_in = space * (indentation_level + 1)

        result = prefix + "{" + line_break
        key_indent = self.get_indent_for_keys(self._children)
        for key in self._children:
            key_prefix = ' '*(key_indent-len(key))
            value = self._children[key]
            # Uncomment to spam types.
            #result += prefix_in + '// '+str(type(value)) + line_break
            result += prefix_in + self._escape(str(key))
            if type(value) is list:
                for i in range(len(value)):
                    if i > 0:
                        result += line_break
                        result += prefix_in + self._escape(str(key))
                    if type(value[i]) is KeyValues:
                        result += line_break
                        result += value[i]._stringify_recursive(indentation, line_break, space, (indentation_level + 1))
                    else:
                        result += key_prefix+self._escape(str(value[i]))
            elif type(value) is KeyValues:
                result += line_break
                result += value._stringify_recursive(indentation, line_break, space, (indentation_level + 1))
            elif type(value) is str or type(value) is int or type(value) is float:
                result += key_prefix+self._escape(str(value))

            result += line_break

        result += prefix + "}"

        return result

    def _escape(self, text, forcequotes=False):
        text = text.replace('\r', '\\r')
        text = text.replace('\n', '\\n')
        for char in "\\\"\r\n":
            text = text.replace(char, '\\' + char)
        for char in ' \t\r\n':
            if char in text or forcequotes:
                return '"{0}"'.format(text)
        return text


    def parent():
        """Return the parent object for this KeyValues
        """

        return self._parent

    def save(self, filename=None):
        """Save the KeyValues to a file on disk
        """

        if filename is None:
            filename = self.filename

        with open(filename, "w") as f:
            f.write(str(self))

    def load(self, filename=None):
        """Load the KeyValues from the given file
        """

        # TODO: improve this implementation

        with open(filename, "r") as f:
            tokenizer = KeyValuesTokenizer(f.read())

            token = tokenizer.next_token()
            if not token or token["type"] != "STRING":
                # TODO: make a better explanation
                raise Exception("Invalid token {0} @ {1}, expecting STRING.".format(token["type"],tokenizer._location()))

            #print('Root node is "{0}"!'.format(token['data']))
            self.__init__(token["data"])

            token = tokenizer.next_token()
            if not token or token["type"] != "BLOCK_BEGIN":
                # TODO: make a better explanation
                raise Exception("Invalid token {0} @ {1}, expecting BLOCK_BEGIN".format(token["type"],tokenizer._location()))

            self._parse(tokenizer)

            # We should have nothing left
            if tokenizer.next_token():
                raise Exception("Unexpected token at file end")

    def _parse(self, tokenizer):
        key = None

        while True:
            token = tokenizer.next_token()
            if not token:
                raise Exception("Unexpected file end")

            if key:
                if token["type"] == "BLOCK_BEGIN":
                    #print("BLOCK_BEGIN")
                    value = KeyValues(key)
                    value._parse(tokenizer)
                    if key in self:
                        if type(self[key]) is list:
                            self[key].append(value)
                        else:
                            self[key]=[self[key],value]
                    else:
                        self[key] = value
                elif token["type"] == "STRING":
                    #print("STRING({0})->VALUE".format(token['data']))
                    if key in self:
                        if type(self[key]) is list:
                            self[key].append(token['data'])
                        else:
                            self[key]=[self[key],token['data']]
                    else:
                        self[key] = token["data"]
                else:
                    # TODO: make a better explanation
                    raise Exception("Invalid token {0} @ {1}".format(token["type"],tokenizer._location()))
                key = None
            else:
                if token["type"] == "BLOCK_END":
                    break
                if token["type"] != "STRING":
                    # TODO: make a better explanation
                    raise Exception("Invalid token")
                #print("STRING({0})->KEY".format(token['data']))
                key = token["data"]


class KeyValuesTokenizer:
    """Parser for KeyValuesTokenizer

    This class is not meant to external use
    """

    def __init__(self, b):
        self._buffer = b
        self._position = 0
        self._last_line_break = 0
        self._line = 1

    def next_token(self):
        while True:
            self._ignore_whitespace()
            if not self._ignore_comment() and not self._ignore_precompiler():
                break

        # Get the next character and check if we got any character
        current = self._current()
        if not current:
            return False

        # Emit any valid tokens
        #print(" current="+current)
        if current == "{":
            self._forward()
            return {"type": "BLOCK_BEGIN"}
        elif current == "}":
            self._forward()
            return {"type": "BLOCK_END"}
        elif current == '#':
            data = self._get_string()
            return {'type': 'PRECOMPILER', 'data':data}
        else:
            data = self._get_string()
            return {"type": "STRING", "data": data}

    def _get_string(self):
        escape = False
        result = ""

        quoted = False
        if self._current() == "\"":
            quoted = True
            self._forward()

        while True:
            current = self._current()

            # Check if we have any character yet
            if not current:
                break

            # These characters are not part of unquoted strings
            if not quoted and current in "{} \t\n\r":
                break

            # Check if it's the end of a quoted string
            if not escape and quoted and current == "\"":
                break

            # Add the character or escape sequence to the result
            if escape:
                escape = False
                if current == "\"":
                    result += "\""
                elif current == "\\":
                    result += "\\"
            elif current == "\\":
                escape = True
            else:
                result += current

            self._forward()

        if quoted:
            self._forward()

        return result

    def _ignore_whitespace(self):
        while True:
            current = self._current()

            if not current:
                break
            if current == "\n":
                # Keep track of this data for debug
                self._last_line_break = self._position
                self._line += 1
            if current not in " \n\t":
                break

            self._forward()


    def _ignore_comment(self):
        if self._current() == '/' and self._next() == '/':
            while self._current() != "\n":
                self._forward()
            return True
        return False

    def _ignore_precompiler(self):
        if self._current() == '#':
            while self._current() != "\n":
                self._forward()
            return True
        return False

    def _current(self):
        if self._position >= len(self._buffer):
            return None

        return self._buffer[self._position]

    def _next(self):
        if (self._position + 1) >= len(self._buffer):
            return None

        return self._buffer[self._position + 1]

    def _forward(self):
        self._position += 1
        return (self._position < len(self._buffer))

    def _location(self):
        return "line {0}, column {1}".format(self._line, (self._position - self._last_line_break))

if __name__ == '__main__':
    kv = KeyValues("kv")

    kv["name"] = "Test Model"
    print("kv[\"name\"] = {}".format(kv["name"]))
    kv["filename"] = "test.mdl"
    print("kv[\"filename\"] = {}".format(kv["filename"]))

    print("len(kv) = {}".format(len(kv)))

    print("\"name\" in kv = {}".format("name" in kv))
    print("\"uncontained_key\" in kv = {}".format("uncontained_key" in kv))

    del kv["name"]
    print("Deleted kv[\"name\"]")

    print("kv items:")
    for key in kv:
        print("  kv[{0}] = {1}".format(key, kv[key]))

    print("\"name\" in kv = {}".format("name" in kv))

    kv_a = KeyValues("kv_a")
    kv_a["name"] = "kv_a"

    kv_b = KeyValues("kv_b")
    kv_b["name"] = "kv_b"
    kv_a["entry"] = kv_b

    kv_c = KeyValues("kv_c")
    kv_c["name"] = "kv_c"
    kv_b["another"] = kv_c

    print(str(kv_a))

    kv_a.save("test.txt")

    kv = KeyValues("test")
    kv.load("test.txt")
    print(kv.stringify())