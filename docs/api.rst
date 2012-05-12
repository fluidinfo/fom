

Fom - API Documentation
=======================

.. contents::
    :backlinks: none


.. automodule:: fom.session
    :members:


.. automodule:: fom.mapping
    :members:


.. automodule:: fom.api
    :members:

    .. autoclass:: fom.api.FluidApi
        :members:

    .. autoclass:: fom.api.ApiBase
        :members: __call__

        .. attribute:: root_path

            The root path against which request paths are calculated

        .. attribute:: db

            The FluidDB that this API is bound to.


.. automodule:: fom.db
    :members: FluidResponse

    .. autoclass:: fom.db.FluidDB
        :members: __call__


